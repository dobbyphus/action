import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

RUN_SCRIPT = Path(__file__).parent.parent / "scripts" / "run.sh"
ACTION_PATH = Path(__file__).parent.parent


class TestRunScript:
    def test_print_logs_dumps_omo_log_file(self):
        log_file = Path(tempfile.gettempdir()) / "oh-my-opencode.log"
        original = log_file.read_text() if log_file.exists() else None

        try:
            log_file.write_text("internal debug line\n")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                fake_bin = tmppath / "bin"
                fake_bin.mkdir()

                fake_opencode = fake_bin / "opencode"
                fake_opencode.write_text(
                    "#!/bin/bash\nprintf 'fake opencode %s\\n' \"$*\"\n"
                )
                fake_opencode.chmod(0o755)

                result = subprocess.run(
                    ["bash", str(RUN_SCRIPT)],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        "ACTION_PATH": str(ACTION_PATH),
                        "PROMPT": "Reply with the single word OK.",
                        "PROMPT_VARS": "{}",
                        "FORMAT_OUTPUT": "false",
                        "OPENCODE_PRINT_LOGS": "true",
                        "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    },
                )

            assert (
                "fake opencode run --print-logs Reply with the single word OK."
                in result.stdout
            )
            assert "internal debug line" in result.stdout
        finally:
            if original is None:
                log_file.unlink(missing_ok=True)
            else:
                log_file.write_text(original)

    def test_runner_debug_enables_print_logs(self):
        log_file = Path(tempfile.gettempdir()) / "oh-my-opencode.log"
        original = log_file.read_text() if log_file.exists() else None

        try:
            log_file.write_text("runner debug line\n")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                fake_bin = tmppath / "bin"
                fake_bin.mkdir()

                fake_opencode = fake_bin / "opencode"
                fake_opencode.write_text(
                    "#!/bin/bash\nprintf 'fake opencode %s\\n' \"$*\"\n"
                )
                fake_opencode.chmod(0o755)

                result = subprocess.run(
                    ["bash", str(RUN_SCRIPT)],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        "ACTION_PATH": str(ACTION_PATH),
                        "PROMPT": "Reply with the single word OK.",
                        "PROMPT_VARS": "{}",
                        "FORMAT_OUTPUT": "false",
                        "RUNNER_DEBUG": "1",
                        "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    },
                )

            assert (
                "fake opencode run --print-logs Reply with the single word OK."
                in result.stdout
            )
            assert "runner debug line" in result.stdout
        finally:
            if original is None:
                log_file.unlink(missing_ok=True)
            else:
                log_file.write_text(original)

    @pytest.mark.parametrize(
        ("omo_filename", "plugin", "stale_filename"),
        [
            ("oh-my-openagent.json", "oh-my-openagent@4.19.1", None),
            ("oh-my-opencode.json", "oh-my-opencode@4.18.0", None),
            (
                "oh-my-opencode.json",
                "oh-my-opencode@4.18.0",
                "oh-my-openagent.json",
            ),
            (
                "oh-my-openagent.json",
                "oh-my-openagent@4.19.1",
                "oh-my-opencode.json",
            ),
        ],
    )
    def test_prompt_append_preserves_sisyphus_model(
        self,
        omo_filename,
        plugin,
        stale_filename,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            fake_bin = tmppath / "bin"
            fake_bin.mkdir()

            fake_opencode = fake_bin / "opencode"
            fake_opencode.write_text(
                "#!/bin/bash\nprintf 'fake opencode %s\\n' \"$*\"\n"
            )
            fake_opencode.chmod(0o755)

            home = tmppath / "home"
            omo_dir = home / ".config" / "opencode"
            omo_dir.mkdir(parents=True)
            (omo_dir / "opencode.json").write_text(json.dumps({"plugin": [plugin]}))
            omo_file = omo_dir / omo_filename
            omo_file.write_text(
                json.dumps(
                    {
                        "agents": {
                            "sisyphus": {
                                "model": "github-copilot/claude-opus-4.6",
                                "variant": "max",
                            }
                        }
                    }
                )
            )
            stale_file = omo_dir / stale_filename if stale_filename else None
            if stale_file:
                stale_file.write_text(
                    '{"agents": {"sisyphus": {"model": "stale/model"}}}'
                )

            result = subprocess.run(
                ["bash", str(RUN_SCRIPT)],
                check=True,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "ACTION_PATH": str(ACTION_PATH),
                    "HOME": str(home),
                    "PROMPT": "Reply with the single word OK.",
                    "PROMPT_VARS": "{}",
                    "FORMAT_OUTPUT": "false",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

            data = json.loads(omo_file.read_text())
            assert (
                data["agents"]["sisyphus"]["model"] == "github-copilot/claude-opus-4.6"
            )
            assert data["agents"]["sisyphus"]["variant"] == "max"
            assert "prompt_append" in data["agents"]["sisyphus"]
            assert "Sisyphus" not in data["agents"]
            if stale_file:
                assert "prompt_append" not in stale_file.read_text()
            assert (
                "Runtime config: agent=sisyphus provider=github-copilot "
                "model=claude-opus-4.6 variant=max" in result.stdout
            )

    def test_provider_error_output_fails_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            fake_bin = tmppath / "bin"
            fake_bin.mkdir()

            fake_opencode = fake_bin / "opencode"
            fake_opencode.write_text(
                "#!/bin/bash\n"
                "printf 'APIError: Your credit balance is too low to access the Anthropic API.\\n' >&2\n"
            )
            fake_opencode.chmod(0o755)

            result = subprocess.run(
                ["bash", str(RUN_SCRIPT)],
                check=False,
                capture_output=True,
                text=True,
                cwd=tmppath,
                env={
                    **os.environ,
                    "ACTION_PATH": str(ACTION_PATH),
                    "PROMPT": "Reply with the single word OK.",
                    "PROMPT_VARS": "{}",
                    "FORMAT_OUTPUT": "false",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

            assert result.returncode == 1
            state = json.loads((tmppath / ".dobbyphus-state.json").read_text())
            assert (
                state["error_summary"] == "LLM provider quota or credit check failed."
            )
            assert state["failed"] is True
