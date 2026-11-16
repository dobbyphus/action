"""Report whether the bot already posted a formal review on a PR head."""

import sys
from pathlib import Path

from verify_review_output import load_reviews

FORMAL_STATES = {"APPROVED", "CHANGES_REQUESTED"}


def has_formal_review(reviews: list[dict], bot_login: str, head_sha: str) -> bool:
    for review in reviews:
        user = review.get("user")
        if (
            isinstance(user, dict)
            and user.get("login") == bot_login
            and review.get("state") in FORMAL_STATES
            and review.get("commit_id") == head_sha
        ):
            return True

    return False


def main() -> None:
    if len(sys.argv) != 4:
        print(
            "Usage: review_guard.py <bot_login> <head_sha> <reviews.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        reviews = load_reviews(Path(sys.argv[3]))
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print("true" if has_formal_review(reviews, sys.argv[1], sys.argv[2]) else "false")


if __name__ == "__main__":
    main()
