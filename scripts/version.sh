#!/bin/bash
set -euo pipefail

if [[ "${OPENCODE_VERSION:-latest}" == "latest" ]]; then
  OPENCODE=$(gh api repos/anomalyco/opencode/releases/latest --jq '.tag_name')
else
  OPENCODE="${OPENCODE_VERSION}"
fi

OMO_INPUT="${OH_MY_OPENCODE_VERSION:-latest}"
if [[ "$OMO_INPUT" =~ ^[A-Za-z][A-Za-z0-9._-]*$ && ! "$OMO_INPUT" =~ ^v[0-9] ]]; then
  OMO="v$(curl -fsSL "https://registry.npmjs.org/oh-my-opencode/$OMO_INPUT" \
    | jq -er '.version')"
else
  OMO="${OH_MY_OPENCODE_VERSION}"
fi

echo "opencode=${OPENCODE:-latest}" >> "$GITHUB_OUTPUT"
echo "oh_my_opencode=${OMO:-latest}" >> "$GITHUB_OUTPUT"
