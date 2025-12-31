"""Tests for detect_mode.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from detect_mode import detect_mode, is_review_request


class TestIsReviewRequest:
    """Tests for is_review_request function."""

    def test_empty_body(self):
        assert is_review_request("", "dobbyphus") is False

    def test_empty_bot_name(self):
        assert is_review_request("@dobbyphus review", "") is False

    def test_no_mention(self):
        assert is_review_request("please review this", "dobbyphus") is False

    def test_no_review_word(self):
        assert is_review_request("@dobbyphus fix this bug", "dobbyphus") is False

    def test_simple_review(self):
        assert is_review_request("@dobbyphus review", "dobbyphus") is True

    def test_review_with_comma(self):
        assert is_review_request("@dobbyphus, review this", "dobbyphus") is True

    def test_review_with_colon(self):
        assert is_review_request("@dobbyphus: can you review this", "dobbyphus") is True

    def test_please_review(self):
        assert is_review_request("@dobbyphus, please review this", "dobbyphus") is True

    def test_review_this_pr(self):
        assert is_review_request("@dobbyphus - review the PR", "dobbyphus") is True

    def test_can_you_review(self):
        assert is_review_request("@dobbyphus can you review this?", "dobbyphus") is True

    def test_review_before_mention(self):
        # "review" appears before mention - still valid
        assert is_review_request("please review @dobbyphus", "dobbyphus") is True

    def test_multiline_review(self):
        body = """Hey @dobbyphus,

Can you please review this change?

Thanks!"""
        assert is_review_request(body, "dobbyphus") is True

    def test_case_insensitive_mention(self):
        assert is_review_request("@Dobbyphus review", "dobbyphus") is True
        assert is_review_request("@DOBBYPHUS review", "dobbyphus") is True

    def test_case_insensitive_review(self):
        assert is_review_request("@dobbyphus REVIEW this", "dobbyphus") is True
        assert is_review_request("@dobbyphus Review this", "dobbyphus") is True

    def test_reviewed_not_matched(self):
        # "reviewed" should not trigger review mode
        assert is_review_request("@dobbyphus I reviewed this", "dobbyphus") is False

    def test_reviewer_not_matched(self):
        # "reviewer" should not trigger review mode
        assert is_review_request("@dobbyphus add me as reviewer", "dobbyphus") is False

    def test_reviewing_not_matched(self):
        assert is_review_request("@dobbyphus I'm reviewing now", "dobbyphus") is False

    def test_review_comments_noun_phrase_not_matched(self):
        assert (
            is_review_request(
                "@dobbyphus look at all the review comments and fix them", "dobbyphus"
            )
            is False
        )

    def test_fix_review_comments_not_matched(self):
        assert (
            is_review_request("@dobbyphus fix the review comments", "dobbyphus")
            is False
        )

    def test_address_review_feedback_not_matched(self):
        assert (
            is_review_request("@dobbyphus address the review feedback", "dobbyphus")
            is False
        )

    def test_code_review_noun_not_matched(self):
        assert (
            is_review_request("@dobbyphus the code review has comments", "dobbyphus")
            is False
        )

    def test_review_threads_not_matched(self):
        assert (
            is_review_request("@dobbyphus handle all review threads", "dobbyphus")
            is False
        )

    def test_under_review_not_matched(self):
        assert (
            is_review_request("@dobbyphus this is under review", "dobbyphus") is False
        )

    def test_partial_bot_name_not_matched(self):
        assert is_review_request("@dobbyphus-bot review", "dobbyphus") is False
        assert is_review_request("@dobbyphus123 review", "dobbyphus") is False

    def test_partial_bot_name_at_end_not_matched(self):
        assert is_review_request("please review @dobbyphus-bot", "dobbyphus") is False
        assert is_review_request("please review @dobbyphus123", "dobbyphus") is False
        assert (
            is_review_request("can you review this @dobbyphus-bot", "dobbyphus")
            is False
        )
        assert (
            is_review_request("review the PR @dobbyphus-extended", "dobbyphus") is False
        )

    def test_different_bot_name(self):
        assert is_review_request("@ai-agent review", "ai-agent") is True
        assert is_review_request("@my_bot review this", "my_bot") is True


class TestDetectMode:
    """Tests for detect_mode function."""

    def test_pull_request_event_always_review(self):
        # Assigned as reviewer - always review mode
        result = detect_mode(
            event_name="pull_request",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="",
        )
        assert result == "review"

    def test_issue_comment_with_review_request(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="@dobbyphus please review this",
        )
        assert result == "review"

    def test_issue_comment_without_review(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="@dobbyphus fix this bug",
        )
        assert result == "agent"

    def test_pr_review_comment_with_review_request(self):
        result = detect_mode(
            event_name="pull_request_review_comment",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="@dobbyphus, can you review this?",
        )
        assert result == "review"

    def test_review_body_used_when_comment_empty(self):
        result = detect_mode(
            event_name="pull_request_review",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="",
            review_body="@dobbyphus review please",
        )
        assert result == "review"

    def test_explicit_review_mode_input(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="review",
            bot_name="dobbyphus",
            comment_body="@dobbyphus fix this",
        )
        assert result == "review"

    def test_explicit_custom_mode_input(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="custom",
            bot_name="dobbyphus",
            comment_body="@dobbyphus do something",
        )
        assert result == "custom"

    def test_default_agent_mode(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="@dobbyphus implement this feature",
        )
        assert result == "agent"

    def test_workflow_dispatch_default_agent(self):
        result = detect_mode(
            event_name="workflow_dispatch",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body="",
        )
        assert result == "agent"

    def test_none_bodies(self):
        result = detect_mode(
            event_name="issue_comment",
            input_mode="agent",
            bot_name="dobbyphus",
            comment_body=None,
            review_body=None,
        )
        assert result == "agent"
