#!/usr/bin/env python3

import os
import subprocess
import tempfile
from pathlib import Path


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
