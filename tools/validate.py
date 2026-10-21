#!/usr/bin/env python3
"""Check the repository before it is pushed: run `python3 tools/validate.py` (CI runs it too).

- every plugin has .claude-plugin/plugin.json whose name matches its folder, and is listed in
  .claude-plugin/marketplace.json (and every listed plugin exists);
- every skill has SKILL.md with front matter: `name` equal to the folder name (lowercase letters,
  digits, hyphens) and a `description` of at most 1024 characters;
- skill names are unique across plugins (installers put them in one folder);
- no text file contains a personal absolute path or something that looks like a secret.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TEXT = {".md", ".py", ".sh", ".json", ".css", ".html", ".swift", ".yml", ".yaml", ".txt", ".csv"}
SECRET = re.compile(r"(dapi[0-9a-f]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_\w{30,}|sk-ant-[\w-]{20,}"
                    r"|sk-[A-Za-z0-9]{40,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
HOME_PATH = re.compile(r"(/Users/[a-z][\w.-]*|/home/[a-z][\w.-]*|C:\\Users\\)", re.I)
SKIP_DIRS = {".git", "vendor", "node_modules", "__pycache__", ".cache"}

errors: list[str] = []


def err(path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        err(path, "missing front matter (--- … ---) at the top")
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def check_plugins() -> None:
    market_file = ROOT / ".claude-plugin" / "marketplace.json"
    market = json.loads(market_file.read_text(encoding="utf-8"))
    listed = {p["name"]: p["source"] for p in market.get("plugins", [])}
    folders = sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())
    seen_skills: dict[str, Path] = {}
    for folder in folders:
        manifest = folder / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            err(folder, "missing .claude-plugin/plugin.json")
        elif json.loads(manifest.read_text(encoding="utf-8")).get("name") != folder.name:
            err(manifest, f"name must be {folder.name!r}")
        if listed.get(folder.name) != f"./plugins/{folder.name}":
            err(market_file, f"plugin {folder.name!r} missing, or source is not ./plugins/{folder.name}")
        skills = sorted(p for p in (folder / "skills").glob("*/") if p.is_dir())
        if not skills:
            err(folder, "no skills/<name>/SKILL.md")
        for skill in skills:
            check_skill(skill)
            if skill.name in seen_skills:
                err(skill, f"skill name also used in {seen_skills[skill.name].relative_to(ROOT)}")
            seen_skills[skill.name] = skill
    for name in listed:
        if not (ROOT / "plugins" / name).is_dir():
            err(market_file, f"lists plugin {name!r} but plugins/{name} does not exist")


def check_skill(skill: Path) -> None:
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        err(skill, "missing SKILL.md")
        return
    fields = front_matter(skill_md)
    name, description = fields.get("name", ""), fields.get("description", "")
    if name != skill.name:
        err(skill_md, f"name {name!r} must equal the folder name {skill.name!r}")
    if not NAME.match(skill.name):
        err(skill, "folder name must be lowercase letters, digits and hyphens")
    if not description:
        err(skill_md, "missing description")
    elif len(description) > 1024:
        err(skill_md, f"description is {len(description)} characters (max 1024)")


def check_text_files() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path == Path(__file__).resolve():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if SECRET.search(line):
                err(path, f"line {number}: looks like a secret")
            if HOME_PATH.search(line):
                err(path, f"line {number}: personal absolute path")


def main() -> int:
    check_plugins()
    check_text_files()
    for line in errors:
        print(f"error  {line}")
    print(f"{len(errors)} problem(s)" if errors else "ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
