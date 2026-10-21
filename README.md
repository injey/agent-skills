# agent-skills

Reusable skills for AI coding agents: Claude Code, Cursor, and any agent that reads the
[Agent Skills](https://agentskills.io) `SKILL.md` format. Skills are grouped into **plugins** by theme.
Each skill is a self-contained folder that works the same in every agent.

## Catalogue

| Plugin | Skill | What it does |
| --- | --- | --- |
| `doc-tools` | [`markdown-docs`](plugins/doc-tools/skills/markdown-docs/SKILL.md) | Markdown → styled HTML + PDF documents (cover, contents, page numbers, callouts, Mermaid), and `*.slides.md` → 16:9 HTML decks + PDF. Themeable per project. |
| `doc-tools` | [`story-docs`](plugins/doc-tools/skills/story-docs/SKILL.md) | A linked static site of epic and story notes (main page → epic → story and back), rendered to HTML. Needs `markdown-docs`. |
| `doc-tools` | [`csv-to-html`](plugins/doc-tools/skills/csv-to-html/SKILL.md) | Any CSV → one offline, interactive HTML table (sort, filter, search, export). |

## Install

### Claude Code: plugin marketplace (recommended)

```text
/plugin marketplace add injey/agent-skills
/plugin install doc-tools@injey-agent-skills
```

`/plugin marketplace update injey-agent-skills` pulls new versions. (The marketplace is named
`injey-agent-skills` because Claude Code reserves `agent-skills` for Anthropic.) Skills then show as
`doc-tools:markdown-docs` and so on.

### Any agent: `npx skills`

```bash
npx skills add injey/agent-skills                      # pick skills and agents interactively
npx skills add injey/agent-skills --skill markdown-docs
```

### Any agent: install script

```bash
# without cloning
curl -fsSL https://raw.githubusercontent.com/injey/agent-skills/main/install.sh | bash -s -- --agent cursor

# from a clone
git clone https://github.com/injey/agent-skills.git && cd agent-skills
./install.sh --list
./install.sh --agent claude                                         # all skills -> ~/.claude/skills
./install.sh --agent cursor --scope project --project ~/code/app    # -> ~/code/app/.cursor/skills
./install.sh --agent cursor --skill markdown-docs --link            # symlink: `git pull` updates it
./install.sh --dest ~/some/agent/skills                             # any other agent
```

| `--agent` | User scope (all projects) | Project scope |
| --- | --- | --- |
| `claude` | `~/.claude/skills/` | `<project>/.claude/skills/` |
| `cursor` | `~/.cursor/skills/` (the only folder that syncs to Cursor Cloud Agents) | `<project>/.cursor/skills/` |
| `agents` | `~/.agents/skills/` (shared folder read by several agents) | `<project>/.agents/skills/` |

Start a new agent session after installing. In Cursor, type `/` in Agent chat to see the skills.

### Pinned to a version

Use a tagged release (`git clone --branch v0.1.0 …`) or add the repo as a git submodule in a project
and run `install.sh` from it.

## Requirements

Every script needs only Python 3.9+ and its standard library. `markdown-docs` also needs
[pandoc](https://pandoc.org) 3.x and Chrome, Chromium or Edge for PDF output. It needs
`npm i -g @mermaid-js/mermaid-cli` for diagrams, and can use `swift` (macOS, optional) for PDF page
previews. `python3 <skill>/scripts/md2pdf.py doctor` checks them.

## Repository layout

```
.claude-plugin/marketplace.json   lists the plugins (Claude Code marketplace)
plugins/<plugin>/
  .claude-plugin/plugin.json      plugin name, version, description
  skills/<skill>/SKILL.md         one folder per skill, plus its scripts/, templates/, assets/
install.sh                        installer for any agent
tools/validate.py                 checks the repo (CI runs it on every push and PR)
docs/authoring.md                 how to add a skill or plugin
```

## Contributing

See [docs/authoring.md](docs/authoring.md). Run `python3 tools/validate.py` before opening a pull request.

## Licence

[MIT](LICENSE)
