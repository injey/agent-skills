# Changelog

## 0.3.1 (2026-10-27)

- `markdown-docs` (doc-tools 0.1.2): works on Windows. pandoc and Mermaid text is read and written
  as UTF-8, so accents, dashes, curly quotes and emoji no longer break builds; more Chrome and Edge
  install paths are found (32-bit Chrome, per-user Chrome in `%LOCALAPPDATA%`, 64-bit Edge);
  `doctor` checks `pdftoppm` off macOS; SKILL.md covers PowerShell and poppler page previews.

## 0.3.0 (2026-10-21)

- GitHub Copilot support: `install.sh --agent copilot` installs to `~/.copilot/skills` (user) or
  `.github/skills` (project); README covers the Copilot CLI marketplace and VS Code.
- `story-docs` 0.1.1: also finds the markdown-docs engine in `.github/skills` and `~/.copilot/skills`.
- `publish-skill` 0.1.1: also looks for skills in Copilot folders and reports Copilot update commands.

## 0.2.0 (2026-10-21)

- New `skill-tools` plugin with `publish-skill`: publish a new or updated skill from any project to
  your skills repo, with portability and content checks, version bumps, validation and a release.

## 0.1.1 (2026-10-21)

- Marketplace renamed to `injey-agent-skills`: Claude Code reserves `agent-skills` for
  Anthropic, so `/plugin marketplace add` refused it. Install with `doc-tools@injey-agent-skills`.

## 0.1.0 (2026-10-21)

- `doc-tools` plugin: `markdown-docs` (Markdown to HTML/PDF documents and slide decks), `story-docs`
  (linked story and epic notes site), `csv-to-html` (interactive HTML tables from CSV).
- Claude Code marketplace, `install.sh` for Claude Code, Cursor and other agents, validator and CI.
