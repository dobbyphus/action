#!/bin/bash
set -euo pipefail

ACTION_PATH="${ACTION_PATH:-.}"
CONFIG_SCRIPT="$ACTION_PATH/scripts/config.py"

"$CONFIG_SCRIPT"

if [[ -n "${CONFIG_JSON:-}" ]]; then
  mkdir -p "$HOME/.config/opencode"
  echo "$CONFIG_JSON" > "$HOME/.config/opencode/opencode.json"
fi

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  export GH_TOKEN="$GITHUB_TOKEN"
fi
