#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" == "Linux" ]] && ! command -v tmux &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq --no-install-recommends tmux
fi

if [[ ! -x "$HOME/.opencode/bin/opencode" ]]; then
  curl -fsSL https://opencode.ai/install | bash -s -- --version "${OPENCODE_VERSION}"
fi

# Add to current PATH (GITHUB_PATH only affects subsequent steps)
export PATH="$HOME/.opencode/bin:$PATH"
echo "$HOME/.opencode/bin" >> "$GITHUB_PATH"

bunx "oh-my-opencode@${OH_MY_OPENCODE_VERSION:-latest}" install \
  --no-tui \
  --claude="${PROVIDER_ANTHROPIC:-max20}" \
  --chatgpt="${PROVIDER_OPENAI:-no}" \
  --gemini="${PROVIDER_GOOGLE:-no}" \
  --copilot="${PROVIDER_COPILOT:-no}"
