import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import replay_commits
from replay_commits import body_has_issue_reference, is_commit_signed


@pytest.fixture
def replay(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("REPLAY_NEW_BRANCH_ONLY", "true")
    monkeypatch.setattr(sys, "argv", ["replay_commits.py", "start", "main"])
    results = {
        "get_current_branch": "feature",
        "get_default_branch": "main",
        "get_commits": ["local"],
        "get_remote_branch_sha": None,
        "branch_exists_on_remote": False,
        "replay_commit": "signed",
        "create_pull_request": "https://github.com/owner/repo/pull/1",
        "git": "",
        "gh_api": "",
    }
    mocks = {name: Mock(return_value=value) for name, value in results.items()}
    for name, mock in mocks.items():
        monkeypatch.setattr(replay_commits, name, mock)
    return mocks


class TestNewBranchOnly:
    def test_creates_new_ref(self, replay):
        assert replay_commits.main() == 0
        replay["gh_api"].assert_called_once_with(
            "repos/owner/repo/git/refs",
            method="POST",
            input_data={"ref": "refs/heads/feature", "sha": "signed"},
        )

    def test_rejects_existing_branch_before_replay(self, replay):
        replay["get_remote_branch_sha"].return_value = "existing"
        assert replay_commits.main() == 1
        replay["git"].assert_not_called()
        replay["replay_commit"].assert_not_called()
        replay["gh_api"].assert_not_called()

    def test_branch_created_during_replay_never_updates_ref(self, replay):
        replay["branch_exists_on_remote"].return_value = True
        replay["gh_api"].side_effect = subprocess.CalledProcessError(1, "gh")
        with pytest.raises(subprocess.CalledProcessError):
            replay_commits.main()
        assert replay["gh_api"].call_args.kwargs["method"] == "POST"
        replay["gh_api"].assert_called_once()
        replay["create_pull_request"].assert_not_called()

    @pytest.mark.parametrize("value", ["", "tru", "FALSE"])
    def test_invalid_policy_fails_closed(self, replay, monkeypatch, value):
        monkeypatch.setenv("REPLAY_NEW_BRANCH_ONLY", value)
        assert replay_commits.main() == 1
        replay["git"].assert_not_called()
        replay["gh_api"].assert_not_called()

    def test_default_preserves_existing_branch_mode(self, replay, monkeypatch):
        monkeypatch.delenv("REPLAY_NEW_BRANCH_ONLY")
        replay["branch_exists_on_remote"].return_value = True
        assert replay_commits.main() == 0
        assert replay["gh_api"].call_args.kwargs["method"] == "PATCH"


class TestIsCommitSigned:
    @patch("replay_commits.gh_api")
    def test_signed_commit_returns_true(self, mock_gh_api):
        mock_gh_api.return_value = "true"
        assert is_commit_signed("owner/repo", "abc123") is True
        mock_gh_api.assert_called_once_with(
            "repos/owner/repo/commits/abc123",
            jq=".commit.verification.verified",
            check=False,
        )

    @patch("replay_commits.gh_api")
    def test_unsigned_commit_returns_false(self, mock_gh_api):
        mock_gh_api.return_value = "false"
        assert is_commit_signed("owner/repo", "abc123") is False

    @patch("replay_commits.gh_api")
    def test_api_error_returns_false(self, mock_gh_api):
        mock_gh_api.return_value = ""
        assert is_commit_signed("owner/repo", "abc123") is False

    @patch("replay_commits.gh_api")
    def test_null_response_returns_false(self, mock_gh_api):
        mock_gh_api.return_value = "null"
        assert is_commit_signed("owner/repo", "abc123") is False


class TestBodyHasIssueReference:
    def test_no_reference_empty_body(self):
        assert body_has_issue_reference("", "42") is False

    def test_no_reference_empty_issue(self):
        assert body_has_issue_reference("Some body text", "") is False

    def test_closes_lowercase(self):
        assert body_has_issue_reference("Closes #42", "42") is True

    def test_closes_uppercase(self):
        assert body_has_issue_reference("CLOSES #42", "42") is True

    def test_close_singular(self):
        assert body_has_issue_reference("Close #42", "42") is True

    def test_closed(self):
        assert body_has_issue_reference("Closed #42", "42") is True

    def test_fixes(self):
        assert body_has_issue_reference("Fixes #42", "42") is True

    def test_fix(self):
        assert body_has_issue_reference("Fix #42", "42") is True

    def test_fixed(self):
        assert body_has_issue_reference("Fixed #42", "42") is True

    def test_resolves(self):
        assert body_has_issue_reference("Resolves #42", "42") is True

    def test_resolve(self):
        assert body_has_issue_reference("Resolve #42", "42") is True

    def test_resolved(self):
        assert body_has_issue_reference("Resolved #42", "42") is True

    def test_with_colon(self):
        assert body_has_issue_reference("Closes: #42", "42") is True

    def test_multiline_body(self):
        body = "Some description\n\nCloses #42\n\nMore text"
        assert body_has_issue_reference(body, "42") is True

    def test_different_issue_number(self):
        assert body_has_issue_reference("Closes #42", "99") is False

    def test_no_keyword(self):
        assert body_has_issue_reference("Related to #42", "42") is False

    def test_partial_number_match(self):
        assert body_has_issue_reference("Closes #420", "42") is False

    def test_issue_as_substring(self):
        assert body_has_issue_reference("Closes #142", "42") is False

    def test_in_middle_of_text(self):
        body = "This PR fixes #42 by updating the logic"
        assert body_has_issue_reference(body, "42") is True
