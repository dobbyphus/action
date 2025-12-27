#!/usr/bin/env python3
"""Find and output the prompt template."""

import sys
from pathlib import Path


def find_prompt_file(mode: str, prompt_path: Path, action_path: Path) -> Path | None:
    consumer_file = prompt_path / f"{mode}.md"
    if consumer_file.is_file():
        return consumer_file

    action_file = action_path / "prompts" / f"{mode}.md"
    if action_file.is_file():
        return action_file

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: prompt.py <action_path> <prompt_path> <mode>", file=sys.stderr)
        print("   or: prompt.py --prompt <prompt_text>", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--prompt":
        if len(sys.argv) < 3:
            print("Error: --prompt requires a value", file=sys.stderr)
            sys.exit(1)
        print(sys.argv[2])
        return

    if len(sys.argv) < 4:
        print("Usage: prompt.py <action_path> <prompt_path> <mode>", file=sys.stderr)
        sys.exit(1)

    action_path = Path(sys.argv[1])
    prompt_path = Path(sys.argv[2])
    mode = sys.argv[3]

    prompt_file = find_prompt_file(mode, prompt_path, action_path)

    if not prompt_file:
        print(f"Error: No prompt file found for mode '{mode}'", file=sys.stderr)
        print(f"  Tried: {prompt_path / f'{mode}.md'}", file=sys.stderr)
        print(f"  Tried: {action_path / 'prompts' / f'{mode}.md'}", file=sys.stderr)
        sys.exit(1)

    print(prompt_file.read_text())


if __name__ == "__main__":
    main()
