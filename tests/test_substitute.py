#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from substitute import substitute, VAR_PATTERN, TRANSFORM_LIMIT


class TestVarPattern:
    def test_matches_simple_var(self):
        assert VAR_PATTERN.findall("{{ name }}") == ["name"]

    def test_matches_no_spaces(self):
        assert VAR_PATTERN.findall("{{name}}") == ["name"]

    def test_matches_multiple_vars(self):
        assert VAR_PATTERN.findall("{{ a }} and {{ b }}") == ["a", "b"]

    def test_matches_underscore_vars(self):
        assert VAR_PATTERN.findall("{{ my_var }}") == ["my_var"]


class TestSubstitute:
    def test_simple_substitution(self):
        result = substitute("Hello {{ name }}", {"name": "World"})
        assert result == "Hello World"

    def test_multiple_substitutions(self):
        result = substitute("{{ a }} + {{ b }}", {"a": "1", "b": "2"})
        assert result == "1 + 2"

    def test_missing_var_unchanged(self):
        result = substitute("{{ missing }}", {})
        assert result == "{{ missing }}"

    def test_nested_substitution(self):
        result = substitute(
            "{{ outer }}",
            {"outer": "{{ inner }}", "inner": "resolved"},
        )
        assert result == "resolved"

    def test_multi_level_nesting(self):
        result = substitute(
            "{{ a }}",
            {"a": "{{ b }}", "b": "{{ c }}", "c": "final"},
        )
        assert result == "final"

    def test_no_infinite_loop(self):
        result = substitute(
            "{{ a }}",
            {"a": "{{ b }}", "b": "{{ a }}"},
        )
        assert "{{ a }}" in result or "{{ b }}" in result

    def test_preserves_non_var_text(self):
        result = substitute("prefix {{ x }} suffix", {"x": "middle"})
        assert result == "prefix middle suffix"

    def test_empty_template(self):
        result = substitute("", {"x": "value"})
        assert result == ""

    def test_no_vars_in_template(self):
        result = substitute("no variables here", {"x": "value"})
        assert result == "no variables here"
