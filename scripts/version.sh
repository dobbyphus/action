#!/bin/bash
set -euo pipefail

if [[ "${OPENCODE_VERSION:-latest}" == "latest" ]]; then
  OPENCODE=$(gh api repos/sst/opencode/releases/latest --jq '.tag_name')
else
  OPENCODE="${OPENCODE_VERSION}"
fi

if [[ "${OH_MY_OPENCODE_VERSION:-latest}" == "latest" ]]; then
  OMO=$(gh api repos/code-yeongyu/oh-my-opencode/releases/latest --jq '.tag_name')
else
  OMO="${OH_MY_OPENCODE_VERSION}"
fi

echo "opencode=${OPENCODE:-latest}" >> "$GITHUB_OUTPUT"
echo "oh_my_opencode=${OMO:-latest}" >> "$GITHUB_OUTPUT"
