#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from replay_commits import body_has_issue_reference


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
