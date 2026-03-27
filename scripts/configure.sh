#!/bin/bash
set -euo pipefail

ACTION_PATH="${ACTION_PATH:-.}"
CONFIG_SCRIPT="$ACTION_PATH/scripts/config.py"

"$CONFIG_SCRIPT"

CONFIG_DIR="$HOME/.config/opencode"

if [[ -d "$CONFIG_DIR" ]]; then
  shopt -s nullglob
  for config_file in "$CONFIG_DIR"/*; do
    [[ -f "$config_file" ]] || continue
    echo "==> $config_file"
    cat "$config_file"
    echo
  done
  shopt -u nullglob
fi

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  export GH_TOKEN="$GITHUB_TOKEN"
fi
