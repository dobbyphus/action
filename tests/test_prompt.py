#!/usr/bin/env python3

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from prompt import find_prompt_file


class TestFindPromptFile:
    def test_finds_consumer_file_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action" / "prompts"
            consumer_dir.mkdir()
            action_dir.mkdir(parents=True)

            (consumer_dir / "agent.md").write_text("consumer")
            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file("agent", consumer_dir, tmppath / "action")
            assert result == consumer_dir / "agent.md"

    def test_falls_back_to_action_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action" / "prompts"
            consumer_dir.mkdir()
            action_dir.mkdir(parents=True)

            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file("agent", consumer_dir, tmppath / "action")
            assert result == action_dir / "agent.md"

    def test_returns_none_when_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action"
            consumer_dir.mkdir()
            action_dir.mkdir()

            result = find_prompt_file("missing", consumer_dir, action_dir)
            assert result is None

    def test_nonexistent_consumer_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            action_dir = tmppath / "action" / "prompts"
            action_dir.mkdir(parents=True)

            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file(
                "agent",
                tmppath / "nonexistent",
                tmppath / "action",
            )
            assert result == action_dir / "agent.md"
