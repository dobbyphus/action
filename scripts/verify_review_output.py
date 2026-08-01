"""Verify review mode produced a new PR review."""

import json
import sys
from pathlib import Path

REVIEW_CONTEXT_TYPES = {"pr_comment", "pr_opened", "pr_review_request"}


def load_reviews(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} contains invalid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise TypeError(f"{path} must contain a JSON array")

    return [item for item in data if isinstance(item, dict)]


def review_ids_for_actor(reviews: list[dict], actor_login: str) -> set[int]:
    ids = set()

    for review in reviews:
        user = review.get("user")
        review_id = review.get("id")
        if not isinstance(user, dict) or not isinstance(review_id, int):
            continue
        if user.get("login") == actor_login:
            ids.add(review_id)

    return ids


def verify_review_output(
    actor_login: str,
    context_type: str,
    before_path: Path,
    after_path: Path,
) -> tuple[bool, str]:
    if context_type not in REVIEW_CONTEXT_TYPES:
        return True, "review verification skipped for this context"

    before_ids = review_ids_for_actor(load_reviews(before_path), actor_login)
    after_ids = review_ids_for_actor(load_reviews(after_path), actor_login)

    if after_ids - before_ids:
        return True, "review verification succeeded"

    return False, "Review mode completed without posting a new review."


def main() -> None:
    if len(sys.argv) != 5:
        print(
            "Usage: verify_review_output.py <actor_login> <context_type> "
            "<before_reviews.json> <after_reviews.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    actor_login = sys.argv[1]
    context_type = sys.argv[2]
    before_path = Path(sys.argv[3])
    after_path = Path(sys.argv[4])

    try:
        ok, message = verify_review_output(
            actor_login,
            context_type,
            before_path,
            after_path,
        )
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if ok:
        print(message)
        sys.exit(0)

    print(message, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
