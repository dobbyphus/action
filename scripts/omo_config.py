#!/usr/bin/env python3
"""Read and update the oh-my-opencode 5 user config."""

import json
import re
import sys
from pathlib import Path

OPENCODE_BLOCK = "[opencode]"
JSONC_COMMENT = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.DOTALL)
JSONC_TRAILING_COMMA = re.compile(r'("(?:\\.|[^"\\])*")|,(?=\s*[}\]])')


def omo_major_version(version: str | None) -> int | None:
    match = re.match(r"v?(\d+)(?:\.|$)", version or "")
    return int(match.group(1)) if match else None


def user_config_path() -> Path:
    return Path.home() / ".omo" / "omo.jsonc"


def read_jsonc(path: Path) -> dict:
    text = path.read_text()
    for pattern in (JSONC_COMMENT, JSONC_TRAILING_COMMA):
        text = pattern.sub(lambda match: match.group(1) or "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} contains invalid JSONC: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(
        value.get(OPENCODE_BLOCK, {}), dict
    ):
        raise TypeError(
            f"{path} must contain an object with an {OPENCODE_BLOCK} object"
        )
    return value


def write_config(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n")


def main() -> None:
    path = user_config_path()
    try:
        document = read_jsonc(path)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    block = document.setdefault(OPENCODE_BLOCK, {})
    sisyphus = block.setdefault("agents", {}).setdefault("sisyphus", {})
    if len(sys.argv) > 1 and sys.argv[1]:
        sisyphus["prompt_append"] = sys.argv[1]
        write_config(path, document)

    model = sisyphus.get("model")
    if isinstance(model, str):
        provider, _, model_id = model.partition("/")
        variant = sisyphus.get("reasoning") or sisyphus.get("variant", "default")
        print(
            f"Runtime config: agent=sisyphus provider={provider} "
            f"model={model_id} variant={variant}"
        )


if __name__ == "__main__":
    main()
