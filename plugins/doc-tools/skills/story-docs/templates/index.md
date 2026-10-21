# <Project>: story notes

Analysis and plans for the stories in <backlog link or name>. One folder per story ID, for example
`<EPIC>-01/`, and one overview page per epic.

Each story folder holds:

- `README.md`: summary, current issues and planned changes, decisions, next steps and decisions log;
- data files (CSV, with an HTML view) the story produces;
- `tools/`: scripts used, so the analysis can be rerun against a newer commit.

## Epics

<One paragraph: how the epics fit together and the order they run in.> Each epic page links to its
stories; each story links back to its epic and to this page.

| # | Epic | Goal | Stories | Runs after |
| --- | --- | --- | --- | --- |
| 1 | [<EPIC>: <name>](<epic folder>/README.html) | <one sentence> | <count> (<EPIC>-01 … <EPIC>-nn) | — |

## Stories

| Story | Title | Status | Notes |
| --- | --- | --- | --- |
| [<EPIC>‑01](<epic folder>/<EPIC>-01/README.html) | <title> | <one line> | [notes](<epic folder>/<EPIC>-01/README.html) |
