"""Exercise the composite action's context collection with PR events."""

import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

ACTION_YAML = Path(__file__).parent.parent / "action.yaml"


class TestCollectContext:
    @pytest.mark.parametrize("event_name", ["pull_request", "pull_request_target"])
    @pytest.mark.parametrize(
        ("bot_login", "requested_reviewer", "expected_context"),
        [
            ("dobbyphus[bot]", "", "pr_opened"),
            ("", "dobbyphus[bot]", "pr_review_request"),
            ("", "", None),
        ],
        ids=["labeled", "review_requested", "missing_review_author"],
    )
    def test_pull_request_context(
        self,
        event_name: str,
        bot_login: str,
        requested_reviewer: str,
        expected_context: str | None,
    ) -> None:
        step = ACTION_YAML.read_text().split("- name: Collect context", 1)[1]
        step = step.split("\n    - name:", 1)[0]
        script = textwrap.dedent(step.split("      run: |\n", 1)[1])
        context = {
            "inputs.bot_login": bot_login,
            "github.event_name": event_name,
            "github.event.pull_request.number": "42",
            "github.event.pull_request.title": "Fix a regression",
            "github.event.sender.login": "reviewer",
            "github.event.pull_request.user.login": "contributor",
            "github.event.requested_reviewer.login": requested_reviewer,
        }
        step_env = {
            name: context.get(expression, "")
            for name, expression in re.findall(
                r"^        (\w+): \$\{\{ (.*?) \}\}$", step, re.MULTILINE
            )
        }
        script = re.sub(
            r"\$\{\{\s*(.*?)\s*\}\}",
            lambda match: context.get(match[1], ""),
            script,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output"
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", script],
                check=False,
                capture_output=True,
                text=True,
                env={
                    "PATH": os.environ["PATH"],
                    "GITHUB_OUTPUT": str(output),
                    **step_env,
                },
            )
            if expected_context is None:
                assert result.returncode != 0
                assert "Set bot_login" in result.stderr
                assert not output.exists()
                return

            assert result.returncode == 0, result.stderr
            values = dict(
                line.split("=", 1)
                for line in output.read_text().splitlines()
                if "=" in line
            )

        expected = {
            "number": "42",
            "author": "reviewer",
            "comment_id": "",
            "context_type": expected_context,
            "pr_title": "Fix a regression",
            "pr_author": "contributor",
        }
        assert {key: values[key] for key in expected} == expected
