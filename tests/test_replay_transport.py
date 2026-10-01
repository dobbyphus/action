import base64
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import replay_commits


@pytest.mark.parametrize("persisted", [False, True])
def test_replay_fetch_authentication(tmp_path, monkeypatch, persisted):
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    git = replay_commits.git
    git("init", "-q")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--allow-empty",
        "-qm",
        "fixture",
    )
    sha = git("rev-parse", "HEAD")
    git("update-server-info")
    helper = tmp_path / "gh"
    helper.write_text("#!/bin/sh\nprintf 'username=marker\\npassword=helper\\n\\n'\n")
    helper.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    expected = "Basic " + base64.b64encode(b"marker:helper").decode()
    seen = []

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            headers = self.headers.get_all("Authorization", [])
            seen.append(headers)
            if headers != [expected]:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="fixture"')
                self.end_headers()
                return
            super().do_GET()

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setenv("GITHUB_SERVER_URL", url + "/")
        git("remote", "add", "origin", url + "/.git")
        key = f"http.{url}/.extraheader"
        if persisted:
            git("config", key, "Authorization: Basic checkout-marker")
        for name, value in {
            "get_commit_message": "fixture",
            "get_commit_subject": "fixture",
            "get_changed_files": ["file"],
            "create_tree": "tree",
            "create_commit": sha,
        }.items():
            monkeypatch.setattr(replay_commits, name, lambda *_, value=value: value)
        monkeypatch.setattr(
            replay_commits,
            "git",
            lambda *args, **kwargs: git(*args, **kwargs) if "fetch" in args else "",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            assert (
                replay_commits.replay_commit("owner/repo", "original", "parent") == sha
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
    assert [expected] in seen
    assert all(headers in ([], [expected]) for headers in seen)
    if persisted:
        assert git("config", "--get", key) == "Authorization: Basic checkout-marker"
