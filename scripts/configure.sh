#!/bin/bash
set -euo pipefail

ACTION_PATH="${ACTION_PATH:-.}"
CONFIG_SCRIPT="$ACTION_PATH/scripts/config.py"

"$CONFIG_SCRIPT"

OPENCODE_CONFIG="$HOME/.config/opencode/opencode.json"
OMO_CONFIG="$HOME/.config/opencode/oh-my-opencode.json"

if [[ -f "$OPENCODE_CONFIG" ]]; then
  echo "==> $OPENCODE_CONFIG"
  cat "$OPENCODE_CONFIG"
  echo
fi

if [[ -f "$OMO_CONFIG" ]]; then
  echo "==> $OMO_CONFIG"
  cat "$OMO_CONFIG"
  echo
fi

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  export GH_TOKEN="$GITHUB_TOKEN"
fi
