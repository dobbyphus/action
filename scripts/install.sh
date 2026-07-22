#!/bin/bash
set -euo pipefail

opencode_asset_name() {
  local os arch target extension

  case "$(uname -s)" in
    Darwin*) os="darwin" ;;
    Linux*) os="linux" ;;
    MINGW* | MSYS* | CYGWIN*) os="windows" ;;
    *) echo "Unsupported operating system: $(uname -s)" >&2; return 1 ;;
  esac

  arch=$(uname -m)
  [[ "$arch" == "aarch64" ]] && arch="arm64"
  [[ "$arch" == "x86_64" ]] && arch="x64"

  if [[ "$os" == "darwin" && "$arch" == "x64" ]] \
    && [[ "$(sysctl -n sysctl.proc_translated 2>/dev/null || echo 0)" == "1" ]]; then
    arch="arm64"
  fi

  case "$os-$arch" in
    linux-x64 | linux-arm64 | darwin-x64 | darwin-arm64 | windows-x64) ;;
    *) echo "Unsupported OS/architecture: $os/$arch" >&2; return 1 ;;
  esac

  target="$os-$arch"
  extension=".zip"
  [[ "$os" == "linux" ]] && extension=".tar.gz"

  if [[ "$arch" == "x64" ]]; then
    if [[ "$os" == "linux" ]] && ! grep -qwi avx2 /proc/cpuinfo 2>/dev/null; then
      target+="-baseline"
    elif [[ "$os" == "darwin" ]] \
      && [[ "$(sysctl -n hw.optional.avx2_0 2>/dev/null || echo 0)" != "1" ]]; then
      target+="-baseline"
    fi
  fi

  if [[ "$os" == "linux" ]] \
    && { [[ -f /etc/alpine-release ]] || ldd --version 2>&1 | grep -qi musl; }; then
    target+="-musl"
  fi

  printf 'opencode-%s%s\n' "$target" "$extension"
}

install_opencode() {
  local asset release release_tag url digest expected actual tmp_dir archive

  asset=$(opencode_asset_name)
  release_tag="$OPENCODE_VERSION"
  [[ "$release_tag" == v* ]] || release_tag="v$release_tag"
  release=$(gh api "repos/anomalyco/opencode/releases/tags/$release_tag")
  url=$(jq -r --arg asset "$asset" \
    '.assets[] | select(.name == $asset) | .browser_download_url' <<< "$release")
  digest=$(jq -r --arg asset "$asset" \
    '.assets[] | select(.name == $asset) | .digest' <<< "$release")

  if [[ -z "$url" || "$url" == "null" || "$digest" != sha256:* ]]; then
    echo "Release $release_tag has no verified $asset asset" >&2
    return 1
  fi

  tmp_dir=$(mktemp -d)
  trap 'rm -rf "$tmp_dir"' RETURN
  archive="$tmp_dir/$asset"
  curl -fsSL "$url" -o "$archive"

  expected="${digest#sha256:}"
  if command -v sha256sum &>/dev/null; then
    actual=$(sha256sum "$archive")
  elif command -v shasum &>/dev/null; then
    actual=$(shasum -a 256 "$archive")
  else
    echo "No SHA-256 checksum tool found" >&2
    return 1
  fi
  actual="${actual%% *}"
  if [[ "$actual" != "$expected" ]]; then
    echo "Checksum verification failed for $asset" >&2
    return 1
  fi

  if [[ "$asset" == *.tar.gz ]]; then
    tar -xzf "$archive" -C "$tmp_dir"
  else
    unzip -q "$archive" -d "$tmp_dir"
  fi

  mkdir -p "$HOME/.opencode/bin"
  install -m 0755 "$tmp_dir/opencode" "$HOME/.opencode/bin/opencode"
}

if [[ "$(uname -s)" == "Linux" ]] && ! command -v tmux &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq --no-install-recommends tmux
fi

if [[ ! -x "$HOME/.opencode/bin/opencode" ]]; then
  install_opencode
fi

# Add to current PATH (GITHUB_PATH only affects subsequent steps)
export PATH="$HOME/.opencode/bin:$PATH"
echo "$HOME/.opencode/bin" >> "$GITHUB_PATH"

OMO_VERSION="${OH_MY_OPENCODE_VERSION:-latest}"
env -u GH_TOKEN bunx "oh-my-opencode@${OMO_VERSION#v}" install \
  --no-tui \
  --claude="${PROVIDER_ANTHROPIC:-max20}" \
  --openai="${PROVIDER_OPENAI:-no}" \
  --gemini="${PROVIDER_GOOGLE:-no}" \
  --copilot="${PROVIDER_COPILOT:-no}" \
  --opencode-zen="${PROVIDER_OPENCODE_ZEN:-no}" \
  --zai-coding-plan="${PROVIDER_ZAI_CODING_PLAN:-no}" \
  --kimi-for-coding="${PROVIDER_KIMI_FOR_CODING:-no}" \
  --opencode-go="${PROVIDER_OPENCODE_GO:-no}"

echo "OpenCode version: $(opencode --version)"
echo "oh-my-opencode version: ${OMO_VERSION#v}"
