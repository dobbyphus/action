#!/usr/bin/env python3

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from format_output import (
    format_tool_input,
    format_tool_name,
    format_tool_output,
    format_todos,
    get_tool_icon,
    handle_text,
    handle_tool_result,
    handle_tool_use,
    print_group_end,
    print_group_start,
    process_event,
    process_stream,
    truncate_content,
)


class TestGetToolIcon:
    def test_read_icon(self):
        assert get_tool_icon("read") == "📄"

    def test_bash_icon(self):
        assert get_tool_icon("bash") == "🔨"

    def test_case_insensitive(self):
        assert get_tool_icon("READ") == "📄"
        assert get_tool_icon("Bash") == "🔨"

    def test_unknown_tool_default(self):
        assert get_tool_icon("unknown_tool") == "🔧"

    def test_lsp_tools(self):
        assert get_tool_icon("lsp_diagnostics") == "🔬"
        assert get_tool_icon("lsp_hover") == "🔬"


class TestFormatToolName:
    def test_simple_name(self):
        assert format_tool_name("read") == "Read"

    def test_underscore_name(self):
        assert format_tool_name("lsp_diagnostics") == "Lsp Diagnostics"

    def test_multiple_underscores(self):
        assert format_tool_name("ast_grep_search") == "Ast Grep Search"


class TestTruncateContent:
    def test_short_content_unchanged(self):
        content = "line1\nline2\nline3"
        assert truncate_content(content, max_lines=10) == content

    def test_long_content_truncated(self):
        lines = [f"line{i}" for i in range(100)]
        content = "\n".join(lines)
        result = truncate_content(content, max_lines=5)
        assert "line0" in result
        assert "line4" in result
        assert "line5" not in result
        assert "(95 more lines)" in result

    def test_exact_limit(self):
        content = "line1\nline2\nline3"
        result = truncate_content(content, max_lines=3)
        assert result == content


class TestFormatTodos:
    def test_empty_list(self):
        assert format_todos([]) == ""

    def test_single_pending(self):
        todos = [{"content": "Do something", "status": "pending"}]
        assert format_todos(todos) == "⬚ Do something"

    def test_single_completed(self):
        todos = [{"content": "Done task", "status": "completed"}]
        assert format_todos(todos) == "✅ Done task"

    def test_single_in_progress(self):
        todos = [{"content": "Working on it", "status": "in_progress"}]
        assert format_todos(todos) == "🔄 Working on it"

    def test_multiple_todos(self):
        todos = [
            {"content": "First", "status": "completed"},
            {"content": "Second", "status": "in_progress"},
            {"content": "Third", "status": "pending"},
        ]
        result = format_todos(todos)
        assert "✅ First" in result
        assert "🔄 Second" in result
        assert "⬚ Third" in result

    def test_unknown_status(self):
        todos = [{"content": "Unknown", "status": "weird"}]
        assert format_todos(todos) == "• Unknown"


class TestFormatToolOutput:
    def test_todowrite_formats_todos(self):
        tool_input = {
            "todos": [
                {"content": "Task 1", "status": "completed"},
                {"content": "Task 2", "status": "pending"},
            ]
        }
        result = format_tool_output("todowrite", tool_input, "ignored")
        assert "✅ Task 1" in result
        assert "⬚ Task 2" in result

    def test_bash_shows_command_and_output(self):
        result = format_tool_output("bash", {"command": "echo hello"}, "hello\n")
        assert result == "$ echo hello\nhello\n"

    def test_bash_shows_command_only_when_no_output(self):
        result = format_tool_output("bash", {"command": "true"}, "")
        assert result == "$ true"

    def test_other_tool_returns_output(self):
        result = format_tool_output("read", {}, "file contents")
        assert result == "file contents"

    def test_empty_output(self):
        result = format_tool_output("read", {}, "")
        assert result == ""


class TestFormatToolInput:
    def test_read_file_path(self):
        result = format_tool_input("read", {"filePath": "/path/to/file.py"})
        assert result == "/path/to/file.py"

    def test_bash_uses_description(self):
        result = format_tool_input(
            "bash", {"command": "ls -la", "description": "List files"}
        )
        assert result == "List files"

    def test_bash_falls_back_to_command(self):
        result = format_tool_input("bash", {"command": "ls -la"})
        assert result == "ls -la"

    def test_bash_command_long_truncated(self):
        long_cmd = "x" * 100
        result = format_tool_input("bash", {"command": long_cmd})
        assert len(result) == 63
        assert result.endswith("...")

    def test_grep_pattern(self):
        result = format_tool_input("grep", {"pattern": "TODO"})
        assert result == "TODO"

    def test_glob_pattern(self):
        result = format_tool_input("glob", {"pattern": "**/*.py"})
        assert result == "**/*.py"

    def test_task_description(self):
        result = format_tool_input("task", {"description": "Find auth code"})
        assert result == "Find auth code"

    def test_todowrite_empty(self):
        result = format_tool_input("todowrite", {"todos": []})
        assert result == ""

    def test_webfetch_url_short(self):
        result = format_tool_input("webfetch", {"url": "https://example.com/page"})
        assert result == "https://example.com/page"

    def test_webfetch_url_long_truncated(self):
        long_url = "https://example.com/" + "a" * 50
        result = format_tool_input("webfetch", {"url": long_url})
        assert len(result) == 53
        assert result.endswith("...")

    def test_unknown_tool_empty(self):
        result = format_tool_input("unknown", {"foo": "bar"})
        assert result == ""


class TestPrintGroupCommands:
    def test_group_start(self):
        output = io.StringIO()
        print_group_start("Test Title", output)
        assert output.getvalue() == "::group::Test Title\n"

    def test_group_end(self):
        output = io.StringIO()
        print_group_end(output)
        assert output.getvalue() == "::endgroup::\n"


class TestHandleToolUse:
    def test_tool_with_output(self):
        output = io.StringIO()
        part = {
            "tool": "read",
            "state": {
                "input": {"filePath": "/test/file.py"},
                "output": "file contents here",
            },
        }
        handle_tool_use(part, output)
        result = output.getvalue()
        assert "::group::📄 Read: /test/file.py" in result
        assert "file contents here" in result
        assert "::endgroup::" in result

    def test_tool_without_output(self):
        output = io.StringIO()
        part = {"tool": "todoread", "state": {"input": {}, "output": ""}}
        handle_tool_use(part, output)
        result = output.getvalue()
        assert "::group::📋 Todoread" in result
        assert "::endgroup::" in result

    def test_unknown_tool(self):
        output = io.StringIO()
        part = {
            "tool": "custom_tool",
            "state": {"input": {"data": "test"}, "output": "result"},
        }
        handle_tool_use(part, output)
        result = output.getvalue()
        assert "🔧" in result
        assert "Custom Tool" in result

    def test_legacy_format_fallback(self):
        output = io.StringIO()
        part = {"name": "read", "input": {"filePath": "/test/file.py"}}
        handle_tool_use(part, output)
        result = output.getvalue()
        assert "::group::📄 Read: /test/file.py" in result


class TestHandleToolResult:
    def test_result_with_content(self):
        output = io.StringIO()
        part = {"content": "File contents here"}
        handle_tool_result(part, output)
        result = output.getvalue()
        assert "---" in result
        assert "File contents here" in result
        assert "::endgroup::" in result

    def test_result_empty_content(self):
        output = io.StringIO()
        part = {"content": ""}
        handle_tool_result(part, output)
        result = output.getvalue()
        assert "---" not in result
        assert "::endgroup::" in result


class TestHandleText:
    def test_text_with_content(self):
        output = io.StringIO()
        part = {"text": "Agent response here"}
        handle_text(part, output)
        assert output.getvalue() == "Agent response here\n"

    def test_text_whitespace_only(self):
        output = io.StringIO()
        part = {"text": "   \n  "}
        handle_text(part, output)
        assert output.getvalue() == ""

    def test_text_empty(self):
        output = io.StringIO()
        part = {"text": ""}
        handle_text(part, output)
        assert output.getvalue() == ""


class TestProcessEvent:
    def test_tool_use_event(self):
        output = io.StringIO()
        event = {
            "type": "tool_use",
            "part": {"name": "bash", "input": {"command": "echo hello"}},
        }
        process_event(event, output)
        assert "::group::" in output.getvalue()

    def test_tool_result_event(self):
        output = io.StringIO()
        event = {"type": "tool_result", "part": {"content": "hello"}}
        process_event(event, output)
        assert "::endgroup::" in output.getvalue()

    def test_text_event(self):
        output = io.StringIO()
        event = {"type": "text", "part": {"text": "Response"}}
        process_event(event, output)
        assert "Response" in output.getvalue()

    def test_unknown_event_type_passthrough(self):
        output = io.StringIO()
        event = {"type": "unknown_event", "part": {"data": "test"}}
        process_event(event, output)
        result = output.getvalue()
        assert "unknown_event" in result
        assert "test" in result

    def test_step_start_skipped(self):
        output = io.StringIO()
        event = {"type": "step_start", "part": {"id": "123"}}
        process_event(event, output)
        assert output.getvalue() == ""

    def test_step_finish_skipped(self):
        output = io.StringIO()
        event = {"type": "step_finish", "part": {"id": "123"}}
        process_event(event, output)
        assert output.getvalue() == ""


class TestProcessStream:
    def test_multiple_events(self):
        stream = io.StringIO(
            '{"type":"tool_use","part":{"name":"read","input":{"filePath":"test.py"}}}\n'
            '{"type":"tool_result","part":{"content":"file content"}}\n'
            '{"type":"text","part":{"text":"Done"}}\n'
        )
        output = io.StringIO()
        process_stream(stream, output)
        result = output.getvalue()
        assert "::group::" in result
        assert "::endgroup::" in result
        assert "Done" in result

    def test_empty_lines_skipped(self):
        stream = io.StringIO('\n\n{"type":"text","part":{"text":"Hello"}}\n\n')
        output = io.StringIO()
        process_stream(stream, output)
        assert "Hello" in output.getvalue()

    def test_invalid_json_passthrough(self):
        stream = io.StringIO("not json\n")
        output = io.StringIO()
        process_stream(stream, output)
        assert "not json" in output.getvalue()

    def test_mixed_valid_invalid(self):
        stream = io.StringIO(
            'plain text line\n{"type":"text","part":{"text":"Valid JSON"}}\n'
        )
        output = io.StringIO()
        process_stream(stream, output)
        result = output.getvalue()
        assert "plain text line" in result
        assert "Valid JSON" in result
