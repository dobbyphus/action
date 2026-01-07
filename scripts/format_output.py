#!/usr/bin/env python3
"""Format opencode JSON output for GitHub Actions logs."""

import json
import shutil
import subprocess
import sys
from typing import IO, TextIO

TOOL_ICONS = {
    "read": "📄",
    "write": "✏️",
    "edit": "✏️",
    "bash": "🔨",
    "grep": "🔍",
    "glob": "🔍",
    "task": "🤖",
    "todowrite": "📋",
    "todoread": "📋",
    "webfetch": "🌐",
    "lsp_diagnostics": "🔬",
    "lsp_hover": "🔬",
    "lsp_goto_definition": "🔬",
    "lsp_find_references": "🔬",
    "ast_grep_search": "🌳",
    "ast_grep_replace": "🌳",
}

DEFAULT_ICON = "🔧"


def get_tool_icon(tool_name: str) -> str:
    """Get icon for a tool, case-insensitive."""
    return TOOL_ICONS.get(tool_name.lower(), DEFAULT_ICON)


def format_tool_name(name: str) -> str:
    """Format tool name for display."""
    return name.replace("_", " ").title()


def truncate_content(content: str, max_lines: int = 50) -> str:
    """Truncate content if too long."""
    lines = content.split("\n")
    if len(lines) <= max_lines:
        return content
    return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"


def format_tool_input(tool_name: str, tool_input: dict) -> str:
    """Format tool input for the group title."""
    name_lower = tool_name.lower()

    if name_lower in ("read", "write", "edit"):
        return tool_input.get("filePath", "")
    elif name_lower == "bash":
        desc = tool_input.get("description", "")
        if desc:
            return desc
        cmd = tool_input.get("command", "")
        return cmd[:60] + "..." if len(cmd) > 60 else cmd
    elif name_lower in ("grep", "glob"):
        pattern = tool_input.get("pattern", "")
        return pattern[:40] + "..." if len(pattern) > 40 else pattern
    elif name_lower == "task":
        return tool_input.get("description", "")
    elif name_lower in ("todowrite", "todoread"):
        return ""
    elif name_lower == "webfetch":
        url = tool_input.get("url", "")
        return url[:50] + "..." if len(url) > 50 else url

    return ""


def print_group_start(title: str, output: TextIO = sys.stdout) -> None:
    print(f"::group::{title}", file=output, flush=True)


def print_group_end(output: TextIO = sys.stdout) -> None:
    print("::endgroup::", file=output, flush=True)


STATUS_ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⬚",
    "cancelled": "❌",
}


def format_todos(todos: list) -> str:
    lines = []
    for todo in todos:
        status = todo.get("status", "pending")
        content = todo.get("content", "")
        icon = STATUS_ICONS.get(status, "•")
        lines.append(f"{icon} {content}")
    return "\n".join(lines)


def format_tool_output(tool_name: str, tool_input: dict, tool_output: str) -> str:
    name_lower = tool_name.lower()

    if name_lower == "todowrite":
        todos = tool_input.get("todos", [])
        if todos:
            return format_todos(todos)
    elif name_lower == "bash":
        cmd = tool_input.get("command", "")
        output_text = truncate_content(tool_output) if tool_output else ""
        if cmd:
            return f"$ {cmd}\n{output_text}" if output_text else f"$ {cmd}"
        return output_text

    return truncate_content(tool_output) if tool_output else ""


def handle_tool_use(part: dict, output: TextIO = sys.stdout) -> None:
    tool_name = part.get("tool", part.get("name", "unknown"))
    state = part.get("state", {})
    tool_input = state.get("input", part.get("input", {}))
    tool_output = state.get("output", "")

    icon = get_tool_icon(tool_name)
    formatted_name = format_tool_name(tool_name)
    input_summary = format_tool_input(tool_name, tool_input)

    if input_summary:
        title = f"{icon} {formatted_name}: {input_summary}"
    else:
        title = f"{icon} {formatted_name}"

    print_group_start(title, output)

    formatted_output = format_tool_output(tool_name, tool_input, tool_output)
    if formatted_output:
        print(formatted_output, file=output, flush=True)

    print_group_end(output)


def handle_tool_result(part: dict, output: TextIO = sys.stdout) -> None:
    content = part.get("content", "")

    if content:
        print("---", file=output, flush=True)
        print(truncate_content(content), file=output, flush=True)

    print_group_end(output)


def handle_text(part: dict, output: TextIO = sys.stdout) -> None:
    text = part.get("text", "")
    if text.strip():
        print(text, file=output, flush=True)


SKIP_EVENT_TYPES = {"step_start", "step_finish"}


def process_event(event: dict, output: TextIO = sys.stdout) -> None:
    event_type = event.get("type", "")
    part = event.get("part", {})

    if event_type in SKIP_EVENT_TYPES:
        return
    elif event_type == "tool_use":
        handle_tool_use(part, output)
    elif event_type == "tool_result":
        handle_tool_result(part, output)
    elif event_type == "text":
        handle_text(part, output)
    else:
        print(json.dumps(event), file=output, flush=True)


def process_stream(stream: IO[str], output: TextIO = sys.stdout) -> None:
    for line in stream:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
            process_event(event, output)
        except json.JSONDecodeError:
            print(line, file=output, flush=True)


def run_opencode(prompt: str, output: TextIO = sys.stdout) -> int:
    base_cmd = ["opencode", "run", "--format", "json", prompt]

    # Use stdbuf to force line-buffered output from opencode
    stdbuf = shutil.which("stdbuf")
    if stdbuf:
        cmd = [stdbuf, "-oL"] + base_cmd
    else:
        cmd = base_cmd

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if process.stdout:
        process_stream(process.stdout, output)

    return process.wait()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: format_output.py <prompt>", file=sys.stderr)
        print("       opencode run --format json | format_output.py -", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "-":
        process_stream(sys.stdin, sys.stdout)
    else:
        prompt = sys.argv[1]
        exit_code = run_opencode(prompt, sys.stdout)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
