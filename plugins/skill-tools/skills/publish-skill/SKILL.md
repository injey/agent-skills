---
name: publish-skill
description: Publish a new or updated agent skill from any project to your skills repo (an agent-skills style repo, e.g. github.com/injey/agent-skills). Copies the skill in, removes project-specific paths, checks for secrets and employer or customer content, updates the catalogue, changelog and versions, validates, commits, pushes and tags a release. Use when asked to push, publish, sync, share, upload or add a skill (or skill changes) to "my agent-skills repo", "my skills repo" or "agent-skills", or to make a project's skill available to other projects and agents.
---

# Publish a skill to your skills repo

A skills repo holds every reusable skill you build, for Claude Code, Cursor and other `SKILL.md`
agents. It's laid out like [injey/agent-skills](https://github.com/injey/agent-skills): fork it, or
start from it. Its own rules are in `docs/authoring.md`; read that file first, because it wins over
this summary if they differ.

```
<repo>/
  .claude-plugin/marketplace.json     marketplace name: never rename it, it's in users' install commands
  plugins/<plugin>/.claude-plugin/plugin.json
  plugins/<plugin>/skills/<skill>/    one copy per skill; plugins group skills by theme (doc-tools, …)
  README.md  CHANGELOG.md  install.sh  tools/validate.py  docs/authoring.md
```

## 0. Settings (private, per user)

Read `~/.config/publish-skill/config`, a shell-style file that is never committed:

```bash
REPO=injey/agent-skills            # GitHub owner/name of your skills repo
LOCAL=~/dev/agent-skills           # local clone
BLOCK_TERMS='acme|acme-corp|projectx'   # employer, client, customer and internal names, as a grep -E pattern
```

If the file is missing, ask for these three values (suggest that `BLOCK_TERMS` lists the employer,
its products and its customers), write the file, and go on. Never copy `BLOCK_TERMS` into the repo.

## 1. Get the repo ready

```bash
. ~/.config/publish-skill/config; R=$(eval echo "$LOCAL")
[ -d "$R/.git" ] || gh repo clone "$REPO" "$R"
git -C "$R" status --short          # must be clean; if not, show the user and ask
git -C "$R" switch main && git -C "$R" pull --ff-only
M=$(python3 -c "import json;print(json.load(open('$R/.claude-plugin/marketplace.json'))['name'])")   # marketplace name
```

## 2. Find the skill to publish

- Use the skill(s) the user names. Look in the current project's `.claude/skills/`,
  `.cursor/skills/`, `.agents/skills/`, then `~/.claude/skills/` and `~/.cursor/skills/`.
- If the name matches several copies, or none, ask which folder is meant.
- **The source may be a symlink into `$R`** (installed with `install.sh --link`). Then the
  edits are already in the repo: skip the copy in step 3 and go on with the checks.
- **Existing in the repo** (`ls $R/plugins/*/skills/<name>`): it's an update to that plugin.
  Compare first with `diff -ru $R/plugins/<plugin>/skills/<name> <source>`. If the repo has
  changes that the source lacks, which means it was edited elsewhere, show them and ask before
  overwriting.
- **New skill:** choose the plugin whose theme fits. If none fits, propose a new plugin name
  (lowercase, hyphens, a theme such as `data-tools` or `dev-workflow`) and confirm with the user.
  Skill names must be unique across all plugins.

## 3. Make it public-safe and portable (do this on the repo copy, never the source)

Copy it in (the `--delete` stays inside this one skill folder):

```bash
D="$R/plugins/<plugin>/skills/<name>"
mkdir -p "$D"
rsync -a --delete --exclude .DS_Store --exclude __pycache__ --exclude '*.pyc' \
  --exclude .cache --exclude node_modules "<source>/" "${D:?}/"
```

Then check and fix the copy:

- **Paths:** replace `.claude/skills/<name>/…`, `.cursor/skills/<name>/…` and absolute paths
  (`/Users/…`, `/home/…`, `~/dev/…`) with paths relative to the skill folder:
  `<this skill's folder>/scripts/x.py` in prose, and `Path(__file__)`-relative paths in scripts.
- **Front matter:** `name` must equal the folder name, and `description` (at most 1024 characters)
  says what the skill does and when to use it.
- **Leftovers:** remove generated outputs, caches, local test data and anything that only matters
  to the source project.
- **Content scan:** check for secrets, internal hostnames and URLs, and employer, client or
  customer names and branding (logos, brand colours or fonts):

  ```bash
  grep -rniE "dapi|token|secret|passw|apikey|api_key|/Users/|/home/|internal${BLOCK_TERMS:+|$BLOCK_TERMS}" "$D" --exclude-dir=vendor
  ```

  - **Harmless matches:** judge each hit; many are ordinary words, such as CSS "tokens".
  - **Generic wording:** neutralise it yourself, for example swap examples for `PROJ-12`.
  - **Employer-specific content:** if the skill only makes sense with it (an employer's template,
    process or brand), **stop**. Tell the user it should stay in the employer's repo, or offer a
    stripped-down generic version.

## 4. Update the repo files

- `README.md`: add a new skill to the catalogue table, or update its row if what it does changed.
- **Versions** (semver, one release for everything in this run):
  - **Patch** for fixes and wording changes.
  - **Minor** for a new skill or new behaviour.
  - **Major** for breaking changes (a renamed skill, changed script options).

  Bump `version` in the plugin's `plugin.json`, in that plugin's entry in `marketplace.json`, and
  in `marketplace.json` → `metadata.version` (the repo release version).
- `CHANGELOG.md`: a new `## X.Y.Z (YYYY-MM-DD)` section at the top, with one line per skill added
  or changed.

## 5. Validate

```bash
cd "$R"
python3 tools/validate.py                 # names, descriptions, marketplace, secrets, personal paths
claude plugin validate . && claude plugin validate plugins/<plugin>   # if the claude CLI is installed
T=$(mktemp -d) && ./install.sh --dest "$T" --skill <name> && ls "$T/<name>"
```

If the skill has scripts, run their `--help` (or a small sample) from the repo copy. Fix every
problem before going on.

## 6. Commit, push, release

Show the user `git status --short` and a short summary of the diff. The user asked to push, so go
ahead unless step 3 raised something they haven't answered.

```bash
git add -A
git commit -m "<Add|Update> <skill>: <what changed>"     # follow the user's preferences on attribution lines
git push
git tag -a vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z
gh release create vX.Y.Z --title vX.Y.Z --notes "<the CHANGELOG section>"
gh run list -R "$REPO" -L 2                              # CI should pass; check again shortly if still running
```

## 7. Report back

Give the release URL, what changed, and how to get it:

- **Claude Code:** `/plugin marketplace update $M`. For a first install of a new plugin, run
  `/plugin install <plugin>@$M`.
- **Other agents:** `./install.sh --agent cursor --skill <name> --force` from a clone (or the `curl`
  one-liner in the README). Symlinked installs only need a `git pull`.
- **The source project:** its copy is unchanged. If you fixed paths or content in the repo copy,
  ask whether to bring those fixes back into the source.
