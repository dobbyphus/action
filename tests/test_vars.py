#!/usr/bin/env python3

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vars import load_snippets


class TestLoadSnippets:
    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_snippets(Path(tmpdir))
            assert result == {}

    def test_nonexistent_dir(self):
        result = load_snippets(Path("/nonexistent/path"))
        assert result == {}

    def test_loads_md_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "greeting.md").write_text("Hello!")
            (tmppath / "farewell.md").write_text("Goodbye!")

            result = load_snippets(tmppath)

            assert result == {
                "base_greeting": "Hello!",
                "base_farewell": "Goodbye!",
            }

    def test_ignores_non_md_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "valid.md").write_text("content")
            (tmppath / "ignored.txt").write_text("ignored")
            (tmppath / "also_ignored.json").write_text("{}")

            result = load_snippets(tmppath)

            assert result == {"base_valid": "content"}
            assert "base_ignored" not in result

    def test_underscore_in_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "my_snippet.md").write_text("content")

            result = load_snippets(tmppath)

            assert "base_my_snippet" in result
