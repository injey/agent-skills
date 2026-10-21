# Adding a skill or plugin

## Where it goes

- **A skill** is a folder `plugins/<plugin>/skills/<skill-name>/` with a `SKILL.md` and any
  `scripts/`, `templates/` or `assets/` it needs.
- **A plugin** is a themed bundle of skills (`doc-tools`, and later for example `data-tools` or
  `dev-workflow`). Add a new plugin only when no existing theme fits. A Claude Code plugin can also
  carry `commands/`, `agents/`, `hooks/` and `.mcp.json` beside `skills/`. Other agents only use the
  skills.

## SKILL.md rules

```markdown
---
name: my-skill              # must equal the folder name; lowercase letters, digits, hyphens
description: What it does and when to use it, with the phrases a user would say. Max 1024 characters.
---

# My skill

Instructions for the agent…
```

- **The description decides when the agent loads the skill.** Say what it does *and* when to use
  it, with trigger phrases.
- **Paths are relative to the skill's own folder** (`scripts/build.py`). Never use
  `.claude/skills/…`, `.cursor/skills/…`, `.github/skills/…` or absolute paths, so one copy works in
  every agent.
- **Scripts use only the standard library** where possible. List any other requirements in the
  skill and in the README.
- **Keep the skill self-contained.** If it uses another skill, look for it beside its own folder
  (`Path(__file__).resolve().parents[2] / "<other-skill>"`), then in the usual skills folders.
- **No secrets, customer names or employer branding.** Projects keep their own branding (for
  example a `.md2pdf/` folder for `markdown-docs`).
- **Skill names must be unique across all plugins**, because installers put every skill in one
  folder.

## Checklist

1. Create the skill folder and `SKILL.md`.
2. New plugin? Add `plugins/<plugin>/.claude-plugin/plugin.json` and list it in
   `.claude-plugin/marketplace.json` with `"source": "./plugins/<plugin>"`.
3. Add the skill to the catalogue in `README.md` and a line to `CHANGELOG.md`.
4. Bump `version` in the plugin's `plugin.json` and in `marketplace.json`. Keep the marketplace
   `name` as `injey-agent-skills`: it is what users type after `@`, and changing it breaks installs.
5. Run `python3 tools/validate.py`, and try it with `./install.sh --dest /tmp/skills-test`.
6. Release: tag `vX.Y.Z` and create a GitHub release (`gh release create vX.Y.Z --generate-notes`).
