#!/bin/bash
set -uo pipefail

ACTION_PATH="${ACTION_PATH:-.}"
PROMPT_PATH="${PROMPT_PATH:-.github/prompts}"

VARS_SCRIPT="$ACTION_PATH/scripts/vars.py"
PROMPT_SCRIPT="$ACTION_PATH/scripts/prompt.py"
SUBSTITUTE_SCRIPT="$ACTION_PATH/scripts/substitute.py"

VARS=$("$VARS_SCRIPT" "$ACTION_PATH" "$PROMPT_PATH" "${PROMPT_VARS:-}")

PROMPT_APPEND=""
for base in github_env comment_formatting file_changes; do
  BASE_FILE="$ACTION_PATH/prompts/base/${base}.md"
  if [[ -f "$BASE_FILE" ]]; then
    CONTENT=$("$SUBSTITUTE_SCRIPT" "$VARS" < "$BASE_FILE")
    PROMPT_APPEND="${PROMPT_APPEND}${CONTENT}"$'\n\n'
  fi
done

if [[ -n "$PROMPT_APPEND" ]]; then
  OMO_FILE="$HOME/.config/opencode/oh-my-opencode.json"
  if [[ -f "$OMO_FILE" ]]; then
    jq --arg append "$PROMPT_APPEND" \
      '.agents.Sisyphus.prompt_append = $append' \
      "$OMO_FILE" > "${OMO_FILE}.tmp" && mv "${OMO_FILE}.tmp" "$OMO_FILE"
  fi
fi

if [[ -n "${PROMPT:-}" ]]; then
  TEMPLATE=$("$PROMPT_SCRIPT" --prompt "$PROMPT")
else
  TEMPLATE=$("$PROMPT_SCRIPT" "$ACTION_PATH" "$PROMPT_PATH" "${MODE:-}")
fi

# Prepend mode-specific keywords to trigger oh-my-opencode modes
KEYWORDS=""
if [[ "${MODE:-}" == "agent" ]]; then
  KEYWORDS="${AGENT_KEYWORDS:-}"
elif [[ "${MODE:-}" == "review" ]]; then
  KEYWORDS="${REVIEW_KEYWORDS:-}"
fi

if [[ -n "$KEYWORDS" ]]; then
  KEYWORDS=$("$SUBSTITUTE_SCRIPT" "$VARS" <<< "$KEYWORDS")
  TEMPLATE="${KEYWORDS}"$'\n'"${TEMPLATE}"
fi

FINAL=$("$SUBSTITUTE_SCRIPT" "$VARS" <<< "$TEMPLATE")
FORMAT_SCRIPT="$ACTION_PATH/scripts/format_output.py"

set +e
if [[ "${FORMAT_OUTPUT:-true}" == "true" ]] && [[ "${GITHUB_ACTIONS:-}" == "true" ]] && [[ -f "$FORMAT_SCRIPT" ]]; then
  python3 "$FORMAT_SCRIPT" "$FINAL"
else
  opencode run "$FINAL"
fi
EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -ne 0 ]]; then
  if [[ -f .dobbyphus-state.json ]]; then
    jq '. + {failed: true}' .dobbyphus-state.json > .dobbyphus-state.tmp \
      && mv .dobbyphus-state.tmp .dobbyphus-state.json
  fi
fi

exit $EXIT_CODE
