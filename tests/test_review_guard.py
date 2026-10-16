import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from review_guard import has_formal_review

BOT = "lambdaphus[bot]"
HEAD = "e5f0f778"


def review(state: str, commit_id: str = HEAD, login: str = BOT) -> dict:
    return {"user": {"login": login}, "state": state, "commit_id": commit_id}


class TestHasFormalReview:
    def test_detects_formal_review_on_head(self):
        assert has_formal_review([review("APPROVED")], BOT, HEAD)
        assert has_formal_review([review("CHANGES_REQUESTED")], BOT, HEAD)

    def test_ignores_comments_other_heads_and_other_users(self):
        reviews = [
            review("COMMENTED"),
            review("APPROVED", commit_id="0ld0ld00"),
            review("APPROVED", login="someone"),
            {"state": "APPROVED", "commit_id": HEAD},
        ]

        assert not has_formal_review(reviews, BOT, HEAD)
