#!/usr/bin/env python3
"""Detect agent mode from event context."""

import os
import re


def is_review_request(body: str, bot_name: str) -> bool:
    """Check if the comment is requesting a review.

    Returns True if:
    1. The comment mentions @bot_name, AND
    2. The comment contains the word "review" (case-insensitive, whole word)

    Args:
        body: The comment or review body text
        bot_name: The bot's mention name (without @)

    Returns:
        True if this is a review request, False otherwise
    """
    if not body or not bot_name:
        return False

    # Check for @bot_name mention (case-insensitive)
    # GitHub usernames can contain alphanumeric and hyphens, so we need to
    # ensure we're not matching a partial username (e.g., @dobbyphus-bot)
    mention_pattern = re.compile(
        rf"@{re.escape(bot_name)}(?![a-zA-Z0-9-])", re.IGNORECASE
    )
    if not mention_pattern.search(body):
        return False

    # Check for "review" as a whole word (not "reviewed", "reviewer", etc.)
    review_pattern = re.compile(r"\breview\b", re.IGNORECASE)
    return bool(review_pattern.search(body))


def detect_mode(
    event_name: str,
    input_mode: str,
    bot_name: str,
    comment_body: str | None = None,
    review_body: str | None = None,
) -> str:
    """Detect the effective mode based on event context.

    Priority:
    1. pull_request event (reviewer assigned) → review
    2. Comment contains @bot_name + "review" → review
    3. Explicit input_mode (if not default "agent") → input_mode
    4. Default → agent

    Args:
        event_name: GitHub event name (e.g., "issue_comment", "pull_request")
        input_mode: The mode input from action configuration
        bot_name: The bot's mention name
        comment_body: Body of issue/PR comment (if applicable)
        review_body: Body of PR review (if applicable)

    Returns:
        The detected mode: "agent" or "review"
    """
    # Assigned as reviewer - use review mode
    if event_name == "pull_request":
        return "review"

    # Check comment/review body for review request
    body = comment_body or review_body or ""
    if is_review_request(body, bot_name):
        return "review"

    # User explicitly set a different mode
    if input_mode and input_mode != "agent":
        return input_mode

    # Default to agent mode
    return "agent"


def main() -> None:
    """Entry point - reads from environment and outputs detected mode."""
    event_name = os.environ.get("EVENT_NAME", "")
    input_mode = os.environ.get("INPUT_MODE", "agent")
    bot_name = os.environ.get("INPUT_BOT_NAME", "ai-agent")
    comment_body = os.environ.get("COMMENT_BODY", "")
    review_body = os.environ.get("REVIEW_BODY", "")

    mode = detect_mode(
        event_name=event_name,
        input_mode=input_mode,
        bot_name=bot_name,
        comment_body=comment_body,
        review_body=review_body,
    )

    print(f"Detected mode: {mode}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"value={mode}\n")


if __name__ == "__main__":
    main()
