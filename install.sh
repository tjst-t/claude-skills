#!/bin/bash
set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SKILL_DIR" ]; then
  echo "Creating skill directory: $SKILL_DIR"
  mkdir -p "$SKILL_DIR"
fi

# Remove stale symlinks for skills that no longer exist in this repo
# (e.g. gui-spec was demoted into sprint/references in the v0.5 refactor).
for link in "$SKILL_DIR"/*; do
  [ -L "$link" ] || continue
  resolved=$(readlink "$link")
  case "$resolved" in
    "$SCRIPT_DIR"/skills/*)
      if [ ! -d "$resolved" ]; then
        echo "Removing stale symlink: $(basename "$link") (target no longer exists)"
        rm "$link"
      fi
      ;;
  esac
done

for skill in "$SCRIPT_DIR"/skills/*/; do
  name=$(basename "$skill")
  target="$SKILL_DIR/$name"
  if [ -L "$target" ]; then
    echo "Updating symlink: $name"
    rm "$target"
  elif [ -e "$target" ]; then
    echo "WARNING: $target already exists and is not a symlink. Skipping."
    continue
  else
    echo "Installing: $name"
  fi
  ln -s "$skill" "$target"
done

echo "Done. Installed skills:"
ls -la "$SKILL_DIR"/ | grep -- '->'
