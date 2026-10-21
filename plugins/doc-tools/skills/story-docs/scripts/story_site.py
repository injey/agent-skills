#!/usr/bin/env python3
"""Check, fix and build a linked story site: main page -> epics -> stories, and back (story-docs skill).

    python3 story_site.py check [ROOT]          report navigation gaps and broken / .pdf / .md links
    python3 story_site.py fix   [ROOT]          rewrite links to .html, add the missing back links
    python3 story_site.py build [ROOT] [--changed] [--all]
                                                render every page to HTML with the markdown-docs engine

ROOT is the stories folder (default: current folder). Layout it expects:

    ROOT/README.md                      main page: what the epics are, links to every epic and story
    ROOT/[<TICKET>-]<EPIC>/README.md    epic overview, e.g. SETTINGS/ or PROJ-12-SETTINGS/ (a tracker
                                        ticket such as PROJ-12 may prefix the folder; the epic is SETTINGS)
    ROOT/<epic folder>/<EPIC>-<n>/      story notes, e.g. PROJ-12-SETTINGS/SETTINGS-03/README.md (plus
                                        data files, tools/)

A flat layout (ROOT/<EPIC>-<n>/ beside the epic folder) still works. Expected links are computed from
where the pages are, so either layout checks the same way.

Rules it enforces (the HTML view is the one people read):
- every relative link points at a .html page, never .md or .pdf;
- the main page links to every epic and story; each epic links to its stories;
- each epic and story has a `::: page-nav` block under its title with its back links (epic -> main
  page; story -> epic and main page). The markdown-docs engine shows it top right, above the contents.
Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

LINK = re.compile(r"(\]\()([^)\s]+)(\))")
STORY_DIR = re.compile(r"^(?P<epic>[A-Z][A-Z0-9]*)-(?P<n>\d+)$")
EPIC_DIR = re.compile(r"^(?:[A-Z][A-Z0-9]*-\d+-)?(?P<epic>[A-Z][A-Z0-9]*)$")   # optional ticket prefix
EXTERNAL = re.compile(r"^[a-z][a-z0-9+.-]*:|^#|^/")
INDEX_NAME = "README.md"
SITE_CSS = Path(__file__).resolve().parents[1] / "assets" / "story-site.css"
# One-word statuses for an epic's Stories table, shown as coloured badges (assets/story-site.css).
STATUSES = ("not-started", "analysed", "in-progress", "in-review", "done", "blocked", "on-hold")
STATUS_BADGE = re.compile(r'<span class="status ([a-z-]+)">([A-Z ]+)</span>')
TABLE_ID_LINK = re.compile(r"(?<=\| )(?:\*\*)?\[[A-Z][A-Z0-9]*-\d+\]\(", re.M)   # "| [SETTINGS-01](" in a table cell


@dataclass
class Site:
    root: Path
    epics: dict[str, Path] = field(default_factory=dict)      # SETTINGS -> PROJ-12-SETTINGS/README.md
    stories: dict[str, Path] = field(default_factory=dict)    # SETTINGS-03 -> PROJ-12-SETTINGS/SETTINGS-03/README.md

    @classmethod
    def load(cls, root: Path) -> "Site":
        site = cls(root)
        candidates: dict[str, Path] = {}
        for page in sorted([*root.glob(f"*/{INDEX_NAME}"), *root.glob(f"*/*/{INDEX_NAME}")]):
            folder = page.parent.name
            if STORY_DIR.match(folder):
                site.stories[folder] = page
            elif page.parent.parent == root and EPIC_DIR.match(folder):
                candidates[EPIC_DIR.match(folder).group("epic")] = page
        # a folder in capitals with no stories of its own (a review page, say) isn't an epic
        site.epics = {e: p for e, p in candidates.items() if any(s.startswith(f"{e}-") for s in site.stories)}
        return site

    def epic_of(self, story: str) -> str:
        return STORY_DIR.match(story).group("epic")

    def link(self, from_page: Path, to_page: Path) -> str:
        """The relative .html link from one page to another."""
        return Path(os.path.relpath(to_page.with_suffix(".html"), from_page.parent)).as_posix()


# --- links ------------------------------------------------------------------------------------

def _targets(page: Path) -> list[str]:
    return [m.group(2) for m in LINK.finditer(page.read_text(encoding="utf-8"))]


def _html_for(page: Path, target: str) -> str | None:
    """The .html form of a relative link to a .md or .pdf page, when that page's source exists."""
    path, _, anchor = target.partition("#")
    stem, dot, ext = path.rpartition(".")
    if not dot or ext not in ("md", "pdf"):
        return None
    if not (page.parent / f"{stem}.md").exists():
        return None
    return f"{stem}.html" + (f"#{anchor}" if anchor else "")


def link_problems(root: Path) -> list[str]:
    problems = []
    for page in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in page.relative_to(root).parts):
            continue
        rel = page.relative_to(root)
        for m in TABLE_ID_LINK.finditer(page.read_text(encoding="utf-8")):
            problems.append(f"{rel}: story ID {m.group(0).strip('*[(')} in a table uses '-'; "
                            "use a non-breaking hyphen (fix does it)")
        for target in _targets(page):
            if EXTERNAL.match(target):
                continue
            path = target.partition("#")[0]
            rel = page.relative_to(root)
            if path.endswith((".md", ".pdf")):
                problems.append(f"{rel}: links to {target} (use the .html page)")
            elif path and not (page.parent / path).exists() and not (
                    path.endswith(".html") and (page.parent / (path[:-5] + ".md")).exists()):
                problems.append(f"{rel}: broken link {target}")
    return problems


def fix_links(root: Path) -> int:
    """Rewrite .md / .pdf page links to .html and collapse 'X (html)' pairs. Returns pages changed."""
    changed = 0
    for page in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in page.relative_to(root).parts):
            continue
        text = page.read_text(encoding="utf-8")

        def swap(m: re.Match) -> str:
            html = None if EXTERNAL.match(m.group(2)) else _html_for(page, m.group(2))
            return f"{m.group(1)}{html}{m.group(3)}" if html else m.group(0)

        new = LINK.sub(swap, text)
        # story IDs linked in table cells keep to one line: "[SETTINGS-01](" -> "[SETTINGS\u201101]("
        new = TABLE_ID_LINK.sub(lambda m: m.group(0).replace("-", "\u2011"), new)
        # "[X](a.html) ([html](a.html))" -> "[X](a.html)"
        new = re.sub(r"(\[[^\]]+\]\(([^)\s]+\.html)\))\s*\(\[html\]\(\2\)\)", r"\1", new)
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    return changed


# --- navigation -------------------------------------------------------------------------------

NAV_BLOCK = re.compile(r"^::: *page-nav *\n(?P<body>.*?)\n::: *$", re.M | re.S)
OLD_NAV_ROW = re.compile(r"^\| *(?:Overview|Navigation) *\|(?P<cell>.*\.\./README\.html.*)\|[ \t]*\n", re.M)


def _nav_links(text: str) -> set[str]:
    block = NAV_BLOCK.search(text)
    return {m.group(2).partition("#")[0] for m in LINK.finditer(block.group("body"))} if block else set()


def _page(site: Site, name: str) -> Path:
    return site.epics.get(name) or site.stories[name]


def _expected_nav(site: Site, name: str) -> list[str]:
    """The page-nav links a page needs: epic -> main page; story -> its epic, main page."""
    page, index = _page(site, name), site.root / INDEX_NAME
    if name in site.epics:
        return [site.link(page, index)]
    epic = site.epic_of(name)
    to_epic = [site.link(page, site.epics[epic])] if epic in site.epics else []
    return to_epic + [site.link(page, index)]


def nav_problems(site: Site) -> list[str]:
    problems = []
    index = site.root / INDEX_NAME
    index_links = {t.partition("#")[0] for t in _targets(index)} if index.exists() else set()
    if not index.exists():
        problems.append(f"{INDEX_NAME}: missing main page")
    for name in [*site.epics, *site.stories]:
        target = site.link(index, _page(site, name))
        if target not in index_links:
            problems.append(f"{INDEX_NAME}: no link to {target}")
    for epic, page in site.epics.items():
        links = {t.partition("#")[0] for t in _targets(page)}
        for story in (s for s in site.stories if site.epic_of(s) == epic):
            if site.link(page, site.stories[story]) not in links:
                problems.append(f"{epic}: no link to {story}")
    for name in [*site.epics, *site.stories]:
        page = _page(site, name)
        text = page.read_text(encoding="utf-8")
        if OLD_NAV_ROW.search(text):
            problems.append(f"{name}: back links in the header table; move them to the page-nav block (fix does it)")
        have = _nav_links(text)
        for target in _expected_nav(site, name):
            if target not in have:
                problems.append(f"{name}: page-nav block has no link to {target}")
    return problems


def status_problems(site: Site) -> list[str]:
    """Each story row in an epic's Stories table has a Status cell with one known badge."""
    problems = []
    for epic, page in site.epics.items():
        for line in page.read_text(encoding="utf-8").splitlines():
            story = re.match(r"^\| \*\*\[([A-Z][A-Z0-9]*)[-\u2011](\d+)\]", line)
            if not story:
                continue
            badge = STATUS_BADGE.search(line)
            name = f"{story.group(1)}-{story.group(2)}"
            if not badge:
                problems.append(f"{epic}: {name} has no status badge (<span class=\"status done\">DONE</span>)")
            elif badge.group(1) not in STATUSES or badge.group(2) != badge.group(1).replace("-", " ").upper():
                problems.append(f"{epic}: {name} has an unknown status {badge.group(0)}; use one of {', '.join(STATUSES)}")
    return problems


def _nav_text(site: Site, name: str) -> str:
    page, index = _page(site, name), site.root / INDEX_NAME
    to_index = f"[All epics and stories]({site.link(page, index)})"
    if name in site.epics:
        return f"[← {to_index[1:]}"
    epic = site.epic_of(name)
    parts = [f"[← {epic} overview]({site.link(page, site.epics[epic])})"] if epic in site.epics else []
    return " · ".join(parts + [to_index])


def fix_navigation(site: Site) -> list[str]:
    """Give every epic and story a page-nav block under its title (moving old Overview / Navigation
    header rows into it). The markdown-docs engine shows the block top right, above the contents."""
    done = []
    for name in [*site.epics, *site.stories]:
        page = _page(site, name)
        text = page.read_text(encoding="utf-8")
        old_row = OLD_NAV_ROW.search(text)
        have = _nav_links(text)
        if not old_row and all(t in have for t in _expected_nav(site, name)):
            continue
        body = old_row.group("cell").strip() if old_row else None
        if old_row:
            text = text[: old_row.start()] + text[old_row.end():]
        if body is None or not all(f"]({t})" in body for t in _expected_nav(site, name)):
            body = _nav_text(site, name)
        block = f"::: page-nav\n{body}\n:::\n"
        if NAV_BLOCK.search(text):
            text = NAV_BLOCK.sub(block.rstrip("\n"), text, count=1)
        else:
            title = re.search(r"^# .*\n", text, re.M)
            at = title.end() if title else 0
            text = text[:at] + "\n" + block + text[at:]
        page.write_text(text, encoding="utf-8")
        done.append(f"{name}: page-nav block set")
    return done


# --- build ------------------------------------------------------------------------------------

def find_md2pdf(root: Path) -> Path:
    engine = Path("markdown-docs") / "scripts" / "md2pdf.py"
    skill_dirs = tuple(Path(d) / "skills" for d in (".claude", ".cursor", ".github", ".copilot", ".agents"))   # Claude Code, Cursor, Copilot, others
    for folder in [root, *root.parents]:
        for skills in skill_dirs:
            candidate = folder / skills / engine
            if candidate.exists():
                return candidate
    beside = Path(__file__).resolve().parents[2] / engine
    for candidate in (beside, *(Path.home() / skills / engine for skills in skill_dirs)):
        if candidate.exists():
            return candidate
    raise SystemExit("markdown-docs engine (md2pdf.py) not found beside this skill, or in .claude/skills, "
                     ".cursor/skills, .github/skills, .copilot/skills or .agents/skills above the stories folder "
                     "or in your home folder")


def build(root: Path, *, changed: bool, everything: bool) -> int:
    engine = find_md2pdf(root)
    pages = sorted(p for p in root.rglob("*.md") if not any(x.startswith(".") for x in p.relative_to(root).parts))
    if not everything:
        pages = [p for p in pages if p.name == INDEX_NAME or p.with_suffix(".html").exists()]
    failed = 0
    for page in pages:
        args = [sys.executable, str(engine), str(page), "--format", "html", "--css", str(SITE_CSS)]
        args += ["--changed"] if changed else []
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            failed += 1
            print(f"FAILED {page.relative_to(root)}: {result.stderr.strip()[:300]}")
    print(f"built {len(pages) - failed} of {len(pages)} pages under {root}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["check", "fix", "build"])
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--changed", action="store_true", help="build: only pages whose .md is newer than the .html")
    parser.add_argument("--all", action="store_true",
                        help="build: every .md, not only pages that already have HTML and the main pages")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    site = Site.load(root)
    if args.command == "check":
        problems = nav_problems(site) + status_problems(site) + link_problems(root)
        print(f"{len(site.epics)} epics, {len(site.stories)} stories under {root}")
        print("\n".join(problems) if problems else "navigation and links OK")
        return 1 if problems else 0
    if args.command == "fix":
        pages = fix_links(root)
        done = fix_navigation(Site.load(root))
        print(f"links rewritten in {pages} page(s)")
        print("\n".join(done) if done else "navigation already complete")
        remaining = nav_problems(Site.load(root)) + status_problems(Site.load(root)) + link_problems(root)
        if remaining:
            print("still to fix by hand:\n" + "\n".join(remaining))
        return 1 if remaining else 0
    return build(root, changed=args.changed, everything=args.all)


if __name__ == "__main__":
    sys.exit(main())
