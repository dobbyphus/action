#!/usr/bin/env python3
"""Detect agent mode from event context."""

import os
import re


# Patterns that indicate an explicit review request.
# These are matched case-insensitively and require the bot to be mentioned.
# The patterns use {bot} as a placeholder for the escaped bot name.
REVIEW_COMMAND_PATTERNS = [
    # @bot review, @bot please review, @bot, review
    r"@{bot}\s*[,:]?\s*(please\s+)?review\b",
    # @bot can/could/would you review
    r"@{bot}\s*[,:]?\s*(can|could|would)\s+you\s+(please\s+)?review\b",
    # can/could/would you review ... @bot
    r"\b(can|could|would)\s+you\s+(please\s+)?review\b.*@{bot}",
    # review this/the PR/changes @bot
    r"\breview\s+(this|the\s+(pr|changes?|code))\s+@{bot}",
    # please review @bot
    r"\bplease\s+review\s+@{bot}",
    # @bot - review (with dash separator)
    r"@{bot}\s*-\s*review\b",
]


def is_review_request(body: str, bot_name: str) -> bool:
    """Check if the comment is explicitly requesting a review.

    Uses whitelist patterns to only match explicit review commands, not
    incidental mentions of the word "review" (e.g., "review comments").

    Returns True if the comment matches one of the review command patterns.

    Args:
        body: The comment or review body text
        bot_name: The bot's mention name (without @)

    Returns:
        True if this is an explicit review request, False otherwise
    """
    if not body or not bot_name:
        return False

    escaped_bot = re.escape(bot_name)

    for pattern_template in REVIEW_COMMAND_PATTERNS:
        pattern = pattern_template.format(bot=escaped_bot)
        if re.search(pattern, body, re.IGNORECASE):
            return True

    return False


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
