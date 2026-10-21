#!/usr/bin/env bash
# Install skills from this repository into an agent's skills folder.
#
#   ./install.sh --list
#   ./install.sh                                    # every skill -> ~/.claude/skills
#   ./install.sh --agent cursor --skill markdown-docs --skill story-docs
#   ./install.sh --agent cursor --scope project --project ~/code/my-app
#   ./install.sh --agent copilot --scope project       # -> .github/skills (shared with the team via git)
#   ./install.sh --plugin doc-tools --link          # symlink, so `git pull` updates the skills
#
# Without a clone:
#   curl -fsSL https://raw.githubusercontent.com/injey/agent-skills/main/install.sh | bash -s -- --agent cursor
set -euo pipefail

REPO_URL="https://github.com/injey/agent-skills.git"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/agent-skills"

agent="claude"; scope="user"; project="$PWD"; dest=""; link=0; force=0; list=0
skills=(); plugins=()

usage() {
  cat <<'EOF'
Usage: install.sh [options]
  --agent claude|cursor|copilot|agents
                                 target agent (default: claude). copilot = ~/.copilot/skills (user) or
                                 .github/skills (project); agents = the shared .agents/skills folder
  --scope user|project           user = home folder, all projects (default); project = one project
  --project DIR                  project root for --scope project (default: current directory)
  --dest DIR                     install into DIR instead (any other agent)
  --skill NAME                   install only this skill (repeatable)
  --plugin NAME                  install only this plugin's skills (repeatable)
  --link                         symlink instead of copy (updates with `git pull`; avoid in repos used on Windows)
  --force                        replace skills that are already installed
  --list                         list plugins and skills, then exit
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --agent) agent="$2"; shift 2 ;;
    --scope) scope="$2"; shift 2 ;;
    --project) project="$2"; shift 2 ;;
    --dest) dest="$2"; shift 2 ;;
    --skill) skills+=("$2"); shift 2 ;;
    --plugin) plugins+=("$2"); shift 2 ;;
    --link) link=1; shift ;;
    --force) force=1; shift ;;
    --list) list=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# Find the repository: beside this script, or a cached clone (curl | bash).
here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$here" ] && [ -d "$here/plugins" ]; then
  root="$here"
else
  if [ -d "$CACHE/.git" ]; then git -C "$CACHE" pull --quiet --ff-only; else git clone --quiet --depth 1 "$REPO_URL" "$CACHE"; fi
  root="$CACHE"
  [ "$link" = 1 ] && echo "note: --link points at the cached clone in $CACHE"
fi

if [ "$list" = 1 ]; then
  for p in "$root"/plugins/*/; do
    echo "$(basename "$p"):"
    for s in "$p"skills/*/; do [ -f "$s/SKILL.md" ] && echo "  $(basename "$s")"; done
  done
  exit 0
fi

if [ -z "$dest" ]; then
  case "$agent" in
    claude) sub=".claude/skills" ;;
    cursor) sub=".cursor/skills" ;;
    copilot) [ "$scope" = project ] && sub=".github/skills" || sub=".copilot/skills" ;;
    agents) sub=".agents/skills" ;;
    *) echo "unknown agent: $agent (use claude, cursor, copilot, agents, or --dest DIR)" >&2; exit 2 ;;
  esac
  case "$scope" in
    user) dest="$HOME/$sub" ;;
    project) dest="$(cd "$project" && pwd)/$sub" ;;
    *) echo "unknown scope: $scope (use user or project)" >&2; exit 2 ;;
  esac
fi
mkdir -p "$dest"

wanted() {  # wanted <list...> -- <item>: true when the list is empty or contains the item
  local item="${*: -1}"; local n=$(($# - 2))
  [ "$n" -eq 0 ] && return 0
  local x; for x in "${@:1:$n}"; do [ "$x" = "$item" ] && return 0; done; return 1
}

installed=0
for p in "$root"/plugins/*/; do
  plugin="$(basename "$p")"
  wanted "${plugins[@]+"${plugins[@]}"}" -- "$plugin" || continue
  for s in "$p"skills/*/; do
    [ -f "$s/SKILL.md" ] || continue
    name="$(basename "$s")"
    wanted "${skills[@]+"${skills[@]}"}" -- "$name" || continue
    target="$dest/$name"
    if [ -e "$target" ] || [ -L "$target" ]; then
      if [ "$force" = 1 ]; then rm -rf "${dest:?}/${name:?}"; else echo "skip   $name (already in $dest; use --force to replace)"; continue; fi
    fi
    if [ "$link" = 1 ]; then ln -s "${s%/}" "$target"; else cp -R "${s%/}" "$target"; fi
    echo "added  $name -> $target"
    installed=$((installed + 1))
  done
done

[ "$installed" -gt 0 ] && echo "Done. Start a new $agent session to pick up the skills." || echo "Nothing installed."
