#!/usr/bin/env python3
"""Load base snippets and merge with user variables."""

import json
import sys
from pathlib import Path


def load_snippets(directory: Path) -> dict:
    snippets = {}

    if not directory.is_dir():
        return snippets

    for file in directory.glob("*.md"):
        var_name = f"base_{file.stem}"
        snippets[var_name] = file.read_text()

    return snippets


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: vars.py <action_path> <prompt_path> [prompt_vars_json]",
            file=sys.stderr,
        )
        sys.exit(1)

    action_path = Path(sys.argv[1])
    prompt_path = Path(sys.argv[2])
    user_vars_json = sys.argv[3] if len(sys.argv) > 3 else "{}"

    action_snippets = load_snippets(action_path / "prompts" / "base")
    consumer_snippets = load_snippets(prompt_path / "base")
    user_vars = json.loads(user_vars_json)

    merged = {**action_snippets, **consumer_snippets, **user_vars}

    print(json.dumps(merged))


if __name__ == "__main__":
    main()
