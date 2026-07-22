#!/bin/bash
set -uo pipefail

ACTION_PATH="${ACTION_PATH:-.}"
PROMPT_PATH="${PROMPT_PATH:-.github/prompts}"
OMO_FILE="$HOME/.config/opencode/oh-my-opencode.json"

is_truthy() {
  local value="${1:-}"
  local lowered
  lowered=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')
  [[ "$lowered" == "true" ]] || [[ "$value" == "1" ]]
}

should_print_logs() {
  is_truthy "${OPENCODE_PRINT_LOGS:-false}" \
    || is_truthy "${RUNNER_DEBUG:-}" \
    || is_truthy "${ACTIONS_STEP_DEBUG:-false}" \
    || is_truthy "${ACTIONS_RUNNER_DEBUG:-false}"
}

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
  if [[ -f "$OMO_FILE" ]]; then
    jq --arg append "$PROMPT_APPEND" \
      '.agents.sisyphus = ((.agents.sisyphus // {}) + {prompt_append: $append})' \
      "$OMO_FILE" > "${OMO_FILE}.tmp" && mv "${OMO_FILE}.tmp" "$OMO_FILE"
  fi
fi

if [[ -f "$OMO_FILE" ]]; then
  jq -r '
    .agents.sisyphus
    | select(type == "object" and (.model | type == "string"))
    | (.model | split("/")) as $model
    | "Runtime config: agent=sisyphus provider=\($model[0]) model=\($model[1:] | join("/")) variant=\(.variant // "default")"
  ' "$OMO_FILE"
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
PRINT_LOG_ARGS=()
PRINT_LOGS=false
RUN_LOG="$(mktemp -t dobbyphus-run.XXXXXX)"

provider_error_summary() {
  local log_file="$1"

  if grep -Eiq 'credit balance|insufficient[_ ]quota' "$log_file"; then
    printf '%s\n' 'LLM provider quota or credit check failed.'
    return 0
  fi

  if grep -Eiq 'invalid x-api-key|incorrect api key|api key[^[:cntrl:]]*invalid' "$log_file"; then
    printf '%s\n' 'LLM provider API key authentication failed.'
    return 0
  fi

  return 1
}

if should_print_logs; then
  export OPENCODE_PRINT_LOGS=true
  PRINT_LOGS=true
  PRINT_LOG_ARGS+=(--print-logs)
fi

set +e
if [[ "${FORMAT_OUTPUT:-true}" == "true" ]] && [[ "${GITHUB_ACTIONS:-}" == "true" ]] && [[ -f "$FORMAT_SCRIPT" ]]; then
  python3 "$FORMAT_SCRIPT" "$FINAL" 2> >(tee "$RUN_LOG" >&2)
  EXIT_CODE=$?
else
  if [[ "$PRINT_LOGS" == "true" ]]; then
    opencode run --print-logs "$FINAL" 2> >(tee "$RUN_LOG" >&2)
  else
    opencode run "$FINAL" 2> >(tee "$RUN_LOG" >&2)
  fi
  EXIT_CODE=$?
fi
set -e

ERROR_SUMMARY=""
if ERROR_SUMMARY=$(provider_error_summary "$RUN_LOG"); then
  jq -n --arg summary "$ERROR_SUMMARY" \
    '{error_summary: $summary, failed: true}' > .dobbyphus-state.json
  if [[ $EXIT_CODE -eq 0 ]]; then
    EXIT_CODE=1
  fi
fi

rm -f "$RUN_LOG"

if [[ "$PRINT_LOGS" == "true" ]]; then
  OMO_LOG_FILE="$(python3 -c 'import tempfile; print(tempfile.gettempdir() + "/oh-my-opencode.log")')"
  if [[ -f "$OMO_LOG_FILE" ]]; then
    if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
      echo "::group::oh-my-opencode internal log"
    fi
    cat "$OMO_LOG_FILE"
    if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
      echo "::endgroup::"
    fi
  fi
fi

if [[ $EXIT_CODE -ne 0 ]]; then
  if [[ -f .dobbyphus-state.json ]]; then
    jq '. + {failed: true}' .dobbyphus-state.json > .dobbyphus-state.tmp \
      && mv .dobbyphus-state.tmp .dobbyphus-state.json
  fi
fi

exit "$EXIT_CODE"
