import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).parent.parent
WARMUP_SCRIPT = ROOT / "scripts" / "warmup.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(dedent(content).lstrip())
    path.chmod(0o755)


def test_warmup_waits_for_complete_provider_cache() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        home = tmp_path / "home"
        home.mkdir()
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()

        fake_opencode = fake_bin / "opencode"
        _write_executable(
            fake_opencode,
            """\
                #!/bin/bash
                set -euo pipefail
                while [[ ! -f "$HOME/session-requested" ]]; do
                  sleep 0.05
                done
                mkdir -p "$HOME/.cache/oh-my-opencode"
                printf '%s\n' '{"connected":["github-copilot"]}' \
                  > "$HOME/.cache/oh-my-opencode/connected-providers.json"
                sleep 0.5
                printf '%s\n' \
                  '{"models":{"github-copilot":[{"id":"claude-opus-5"}]},"connected":["github-copilot"]}' \
                  > "$HOME/.cache/oh-my-opencode/provider-models.json"
                sleep 30
                """,
        )

        fake_curl = fake_bin / "curl"
        _write_executable(
            fake_curl,
            """\
                #!/bin/bash
                set -euo pipefail
                if [[ "$*" == *"/global/health"* ]]; then
                  exit 0
                fi
                if [[ "$*" == *"/provider"* ]]; then
                  touch "$HOME/provider-requested"
                  printf '%s\n' \
                    '{"all":[{"id":"github-copilot","models":{"claude-opus-5":{"id":"claude-opus-5"}}}],"connected":["github-copilot"]}'
                  exit 0
                fi
                if [[ "$*" == *"-X POST"* && "$*" == *"/session"* ]]; then
                  touch "$HOME/session-requested"
                  printf '{}\n'
                  exit 0
                fi
                exit 1
                """,
        )

        result = subprocess.run(
            ["bash", str(WARMUP_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
            },
        )

        cache_dir = home / ".cache" / "oh-my-opencode"
        assert result.returncode == 0, result.stderr
        assert (home / "provider-requested").exists()
        assert (cache_dir / "connected-providers.json").exists()
        assert (cache_dir / "provider-models.json").exists()
        assert "scripts/warmup.sh" in (ROOT / "action.yaml").read_text()


def test_warmup_cleans_up_and_exits_on_lifecycle_failures() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        home = tmp_path / "home"
        home.mkdir()
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        log_file = home / "warmup.log"
        provider_snapshot = home / "providers.json"
        curl_started = home / "curl-started"

        fake_mktemp = fake_bin / "mktemp"
        fake_mktemp.write_text(
            dedent(
                """\
                #!/bin/bash
                set -euo pipefail
                if [[ "$*" == *"dobbyphus-warmup"* ]]; then
                  path="$HOME/warmup.log"
                elif [[ "$WARMUP_TEST_MODE" == "allocation-failure" ]]; then
                  exit 1
                else
                  path="$HOME/providers.json"
                fi
                touch "$path"
                printf '%s\n' "$path"
                """
            )
        )
        fake_mktemp.chmod(0o755)

        fake_opencode = fake_bin / "opencode"
        fake_opencode.write_text("#!/bin/bash\nsleep 30\n")
        fake_opencode.chmod(0o755)

        fake_curl = fake_bin / "curl"
        fake_curl.write_text(
            dedent(
                """\
                #!/bin/bash
                set -euo pipefail
                touch "$HOME/curl-started"
                sleep 30
                """
            )
        )
        fake_curl.chmod(0o755)

        env = {
            **os.environ,
            "HOME": str(home),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
        }
        allocation_failure = subprocess.run(
            ["bash", str(WARMUP_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env={**env, "WARMUP_TEST_MODE": "allocation-failure"},
        )

        assert allocation_failure.returncode != 0
        assert not log_file.exists()

        process = subprocess.Popen(
            ["bash", str(WARMUP_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            env={**env, "WARMUP_TEST_MODE": "signal"},
        )
        stderr = ""
        try:
            deadline = time.monotonic() + 2
            while (
                not curl_started.exists()
                and process.poll() is None
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            assert curl_started.exists()

            os.killpg(process.pid, signal.SIGTERM)
            _, stderr = process.communicate(timeout=2)
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if process.poll() is None:
                process.wait()

        assert process.returncode == 143, (process.returncode, stderr)
        assert not log_file.exists()
        assert not provider_snapshot.exists()


def test_warmup_rejects_responses_after_server_exits() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        home = tmp_path / "home"
        cache_dir = home / ".cache" / "oh-my-opencode"
        cache_dir.mkdir(parents=True)
        (cache_dir / "connected-providers.json").write_text(
            '{"connected":["github-copilot"]}'
        )
        (cache_dir / "provider-models.json").write_text(
            '{"models":{"github-copilot":[{"id":"claude-opus-5"}]},'
            '"connected":["github-copilot"]}'
        )

        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        _write_executable(
            fake_bin / "opencode",
            """\
            #!/bin/bash
            printf 'server exited\n' >&2
            touch "$HOME/server-exited"
            """,
        )
        _write_executable(
            fake_bin / "curl",
            """\
            #!/bin/bash
            set -euo pipefail
            if [[ "$*" == *"/global/health"* ]]; then
              while [[ ! -f "$HOME/server-exited" ]]; do
                /bin/sleep 0.01
              done
              /bin/sleep 0.05
              exit 0
            fi
            if [[ "$*" == *"/provider"* ]]; then
              printf '%s\n' \
                '{"all":[{"id":"github-copilot","models":{"claude-opus-5":{"id":"claude-opus-5"}}}],"connected":["github-copilot"]}'
              exit 0
            fi
            printf '{}\n'
            """,
        )

        result = subprocess.run(
            ["bash", str(WARMUP_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
            },
        )

        assert result.returncode != 0
        assert "server exited" in result.stderr


def test_warmup_rejects_provider_cache_without_models() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        home = tmp_path / "home"
        cache_dir = home / ".cache" / "oh-my-opencode"
        cache_dir.mkdir(parents=True)
        (cache_dir / "connected-providers.json").write_text(
            '{"connected":["github-copilot"]}'
        )
        (cache_dir / "provider-models.json").write_text(
            '{"models":{"github-copilot":[]},"connected":["github-copilot"]}'
        )

        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        _write_executable(fake_bin / "opencode", "#!/bin/bash\n/bin/sleep 30\n")
        _write_executable(
            fake_bin / "curl",
            """\
            #!/bin/bash
            if [[ "$*" == *"/provider"* ]]; then
              printf '%s\n' \
                '{"all":[{"id":"github-copilot","models":{"claude-opus-5":{"id":"claude-opus-5"}}}],"connected":["github-copilot"]}'
            else
              printf '{}\n'
            fi
            """,
        )
        _write_executable(fake_bin / "sleep", "#!/bin/bash\nexit 0\n")

        result = subprocess.run(
            ["bash", str(WARMUP_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
            },
        )

        assert result.returncode != 0
        assert "did not create complete provider caches" in result.stderr
