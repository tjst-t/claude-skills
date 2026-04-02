#!/bin/bash
set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SKILL_DIR" ]; then
  echo "Creating skill directory: $SKILL_DIR"
  mkdir -p "$SKILL_DIR"
fi

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
