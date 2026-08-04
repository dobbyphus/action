#!/bin/bash
set -euo pipefail

CACHE_DIR="$HOME/.cache/oh-my-opencode"
CONNECTED_CACHE="$CACHE_DIR/connected-providers.json"
PROVIDER_MODELS_CACHE="$CACHE_DIR/provider-models.json"
PORT="${OPENCODE_WARMUP_PORT:-4096}"
SERVER_URL="http://127.0.0.1:$PORT"
LOG_FILE=""
PROVIDER_SNAPSHOT=""
SERVER_PID=""

# Invoked by the EXIT trap below.
# shellcheck disable=SC2329
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ -n "$LOG_FILE" ]]; then
    rm -f "$LOG_FILE"
  fi
  if [[ -n "$PROVIDER_SNAPSHOT" ]]; then
    rm -f "$PROVIDER_SNAPSHOT"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

LOG_FILE=$(mktemp -t dobbyphus-warmup.XXXXXX)
PROVIDER_SNAPSHOT=$(mktemp -t dobbyphus-providers.XXXXXX)

env -u OPENCODE_CLI_RUN_MODE opencode serve \
  --hostname 127.0.0.1 \
  --port "$PORT" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

fail() {
  echo "$1" >&2
  cat "$LOG_FILE" >&2
  exit 1
}

server_ready=false
for _ in {1..100}; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  if curl -fsS --max-time 1 "$SERVER_URL/global/health" >/dev/null 2>&1; then
    if kill -0 "$SERVER_PID" 2>/dev/null; then
      server_ready=true
    fi
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  sleep 0.1
done

if [[ "$server_ready" != "true" ]]; then
  fail "OpenCode warm-up server failed to start."
fi

if ! curl -fsS --max-time 45 "$SERVER_URL/provider" >"$PROVIDER_SNAPSHOT"; then
  fail "OpenCode warm-up could not read the provider snapshot."
fi

if ! jq -e '
  .connected as $connected
  | (.all // []) as $all
  | ($connected | type == "array" and length > 0)
    and (
      [
        $connected[] as $id
        | $all[]?
        | select(.id == $id and ((.models // {}) | length > 0))
      ]
      | length > 0
    )
' "$PROVIDER_SNAPSHOT" >/dev/null; then
  fail "OpenCode warm-up found no connected provider with models."
fi

if ! curl -fsS --max-time 45 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  "$SERVER_URL/session" >/dev/null; then
  fail "OpenCode warm-up session creation failed."
fi

cache_ready=false
for _ in {1..160}; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  if [[ -f "$CONNECTED_CACHE" && -f "$PROVIDER_MODELS_CACHE" ]] && \
    jq -e \
      --slurpfile snapshot "$PROVIDER_SNAPSHOT" \
      --slurpfile connected "$CONNECTED_CACHE" '
        . as $models
        | $snapshot[0].connected as $expected
        | (($expected - ($connected[0].connected // [])) | length == 0)
          and (($expected - ($models.connected // [])) | length == 0)
          and (
            [
              $expected[] as $provider
              | ($models.models[$provider] // [])
              | length
            ]
            | any(. > 0)
          )
      ' "$PROVIDER_MODELS_CACHE" >/dev/null 2>&1; then
    if kill -0 "$SERVER_PID" 2>/dev/null; then
      cache_ready=true
    fi
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  sleep 0.1
done

if [[ "$cache_ready" != "true" ]]; then
  fail "OpenCode warm-up did not create complete provider caches."
fi
