---
name: story-docs
description: Build and maintain a linked set of story analysis pages (a main page explaining the epics, one overview page per epic, one notes page per story such as SETTINGS-03 or AUTH-12) as HTML, in a fixed format with decisions, status and next steps. Checks and fixes navigation (main page -> epic -> story and back) and makes every link point at .html pages, never .md or .pdf. Use for any project when asked to set up story or epic notes, add a story or epic page, fix broken or PDF links in story pages, rebuild the story HTML, or keep the story site linked.
---

# Story docs

A small static site of working notes, built from Markdown with the markdown-docs engine. People read
the **HTML**, so every page links to other pages' `.html`, never `.md` or `.pdf`. PDFs are optional
prints for sending a single page; nothing links to them.

```
<stories>/
  README.md                   main page: what the project is, the epics table, the stories table
  [<TICKET>-]<EPIC>/          one folder per epic, e.g. REPO/ or PROJ-12-SETTINGS/
    README.md                 epic overview: objective, stories, dependencies, outcome, decisions, next steps
    <EPIC>-<n>/README.md      story notes (format below), plus:
      *.csv -> *.html         data the story produces (CSV, UTF-8 with BOM; HTML view through a CSV-to-HTML tool)
      tools/                  scripts that produced the data, rerunnable
      poc/                    proofs of concept, with their own README.md
```

- **Epic folders** are upper-case names (`SETTINGS`). When the epic is tracked as a ticket in the
  client's tracker, the folder starts with the ticket key: `PROJ-12-SETTINGS` is epic `SETTINGS`.
- **Story folders** are `<EPIC>-<n>` (`SETTINGS-03`), inside their epic's folder.
- An upper-case folder without stories (a review page, say) is an ordinary page, not an epic.
- **Links between pages are relative:** story → epic `../README.html`, story → main page
  `../../README.html`, epic → story `<EPIC>-<n>/README.html`, a story in another epic
  `../../<epic folder>/<EPIC>-<n>/README.html`. `check` computes the expected links from where the
  pages are (the older flat layout, stories beside the epic folder, still checks).
- **Scripts in a story** that find other folders must not count levels to a fixed depth across epics;
  find the stories folder once and join the epic folder (a sibling story in the same epic is `..`).

## Navigation (what `check` enforces)

| Page | Must link to |
| --- | --- |
| Main page | every epic (`<epic folder>/README.html`) and every story (`<epic folder>/<EPIC>-<n>/README.html`) |
| Epic | each of its stories (`<EPIC>-<n>/README.html`); in its page-nav block, the main page |
| Story | in its page-nav block, its epic and the main page |

Back links go in a `page-nav` block right under the page title (not in the header table). The
markdown-docs engine shows it top right, above Contents, and leaves it out of the PDF:

```markdown
# SETTINGS-03: Required settings checked at startup

::: page-nav
[← SETTINGS overview](../README.html) · [All epics and stories](../../README.html)
:::
```

An epic's block holds only `[← All epics and stories](../README.html)`. `fix` adds missing blocks
and moves old `Overview` / `Navigation` header rows into them.

Every relative link is to a file that exists, and `.md` / `.pdf` page links are not allowed. Write
links as `.html` from the start; the engine builds `X.md` into `X.html` beside it.

## Script

`scripts/story_site.py` (standard library only):

```bash
S=<this skill's folder>/scripts/story_site.py
python3 $S check <stories>          # navigation gaps, .md/.pdf links, broken links; exit 1 if any
python3 $S fix   <stories>          # rewrite .md/.pdf page links to .html, add missing back links
python3 $S build <stories>          # HTML for the main pages and every page that already has HTML
python3 $S build <stories> --all    # HTML for every .md page
python3 $S build <stories> --changed  # only pages whose .md is newer than the .html
```

`build` finds the markdown-docs engine (`markdown-docs/scripts/md2pdf.py`) beside this skill, in a
`.claude/skills`, `.cursor/skills`, `.github/skills`, `.copilot/skills` or `.agents/skills` folder above
the stories folder, or in the same folders under your home directory, and renders with the project's theme settings. To render one
page: `python3 <md2pdf.py> <page>.md --format html`. The engine writes `.html` links into the HTML and
`.pdf` links only into the PDF.

`fix` edits the Markdown in place. Back up the folder first if it isn't under version control.

## Workflow

**New project:** copy [templates/index.md](templates/index.md) to `<stories>/README.md` and fill in
the project and epics. For each epic, copy [templates/epic.md](templates/epic.md) to
`<stories>/<EPIC>/README.md`.

**New story:**
1. Copy [templates/story.md](templates/story.md) to `<stories>/<epic folder>/<EPIC>-<n>/README.md`.
2. Add its row to the epic's Stories table and to the main page's Stories table; update the epic's
   story count on the main page.
3. Write the notes (format below). Facts come from scans you ran, not memory.
4. `check`, then `build` (the story's page, its epic and the main page).

**Any edit:** after changing pages, run `check` and `build --changed`. Keep the story status line,
the epic's Stories table and the main page's status row saying the same thing.

## Story status in the epic's Stories table

Columns: Story · Purpose · Depends on · Points · **Status** · **Notes** · **Links**. Status is one
coloured badge; Notes says in one line where the story stands (open decisions, merged PR, what it's
waiting for); Links holds the notes page and the story's data pages. A legend line of all badges sits
above the table (see `templates/epic.md`).

| Badge | Markup | When |
| --- | --- | --- |
| NOT STARTED | `<span class="status not-started">NOT STARTED</span>` | In the backlog; no analysis yet |
| ANALYSED | `<span class="status analysed">ANALYSED</span>` | Analysis or design done (proofs included); building not started |
| IN PROGRESS | `<span class="status in-progress">IN PROGRESS</span>` | Being built, or partly merged |
| IN REVIEW | `<span class="status in-review">IN REVIEW</span>` | Built and pushed; waiting for the team review or PR |
| DONE | `<span class="status done">DONE</span>` | Merged and accepted |
| BLOCKED | `<span class="status blocked">BLOCKED</span>` | Can't move until someone outside the team acts (say who in Notes) |
| ON HOLD | `<span class="status on-hold">ON HOLD</span>` | Paused by decision (say why in Notes) |

`check` reports a story row without a badge or with an unknown one. The colours come from
`assets/story-site.css`, which `build` adds to every page, so they work with any theme. Build story
pages with `story_site.py build`, not with the markdown-docs engine directly.

## Notes format

| Section | Contents |
| --- | --- |
| page-nav block | Back links to the epic and the main page, under the title |
| Header table | Epic · Status (one bold line: agreed vs open, or merged) · Baseline (repo, branch, commit, date; read-only or changed) · Files |
| **Summary** | What the story is for, the key numbers, what earlier decisions already fix |
| **Current issues and planned changes** | # · Current issue · Planned change · Story |
| **Decisions** | ID · Decision · Recommendation · Status (**Agreed** / Open) |
| **Decision details** | One collapsible `<details>` per decision, title ending "(Open)" or "(Agreed)": **Today**, **Recommendation**, **Impact**, **To agree** (numbered yes/no questions with "(Recommended: yes.)") |
| **Next steps** | # · Step · Who; long checklists in collapsible items |
| **Decisions log** | ID · Decision · Date · By |

Rules:
- **Decision IDs are epic-wide** (`S-D1`, `S-D2` … for SETTINGS), so each epic has one register; its
  overview lists the agreed and open ones.
- **Agreed only when the user says so.** A decision stays Open until the user explicitly agrees it.
  Then: Status **Agreed**, "To agree" becomes "Agreed answers (date)", a log row, and the story, epic
  and main-page status lines updated.
- **Final values only.** Once decided, state the decision; don't keep the history of how it changed.
- **Collapsed on screen, open in print:** keep the template's `beforeprint` script after the details.
- **IDs don't wrap:** use a non-breaking hyphen (U+2011) in ID cells (`S‑D14`, `SETTINGS‑02`).
  `check` flags story-ID links in table cells written with a plain `-`, and `fix` converts them
  (the link target keeps the plain hyphen).
- **Tables** for anything with columns; CSV plus its HTML view for long data, linked as `.html`.
- **Writing:** short sentences, plain words, one idea per bullet, acronyms explained on first use.
  The pages are internal working notes.

Project-specific rules (repository, branch rules, where the backlog lives) belong in that project's
own analysis skill, which uses this one for the format and the site.
