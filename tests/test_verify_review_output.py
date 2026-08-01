import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verify_review_output import verify_review_output


class TestVerifyReviewOutput:
    def test_skips_non_review_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            before = tmppath / "before.json"
            after = tmppath / "after.json"
            before.write_text("[]")
            after.write_text("[]")

            ok, message = verify_review_output(
                "lambdaphus[bot]",
                "pr_inline_comment",
                before,
                after,
            )

            assert ok is True
            assert message == "review verification skipped for this context"

    def test_succeeds_when_new_review_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            before = tmppath / "before.json"
            after = tmppath / "after.json"

            before.write_text(
                json.dumps(
                    [
                        {"id": 10, "user": {"login": "lambdaphus[bot]"}},
                    ]
                )
            )
            after.write_text(
                json.dumps(
                    [
                        {"id": 10, "user": {"login": "lambdaphus[bot]"}},
                        {"id": 11, "user": {"login": "lambdaphus[bot]"}},
                    ]
                )
            )

            ok, message = verify_review_output(
                "lambdaphus[bot]",
                "pr_comment",
                before,
                after,
            )

            assert ok is True
            assert message == "review verification succeeded"

    def test_pr_opened_requires_review_from_known_actor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            before = tmppath / "before.json"
            after = tmppath / "after.json"
            before.write_text("[]")
            after.write_text(
                json.dumps([{"id": 10, "user": {"login": "lambdaphus[bot]"}}])
            )

            ok, message = verify_review_output(
                "lambdaphus[bot]",
                "pr_opened",
                before,
                after,
            )

            assert ok is True
            assert message == "review verification succeeded"

    def test_fails_when_no_new_review_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            before = tmppath / "before.json"
            after = tmppath / "after.json"

            before.write_text(
                json.dumps(
                    [
                        {"id": 10, "user": {"login": "lambdaphus[bot]"}},
                    ]
                )
            )
            after.write_text(
                json.dumps(
                    [
                        {"id": 10, "user": {"login": "lambdaphus[bot]"}},
                    ]
                )
            )

            ok, message = verify_review_output(
                "lambdaphus[bot]",
                "pr_review_request",
                before,
                after,
            )

            assert ok is False
            assert message == "Review mode completed without posting a new review."

    def test_ignores_other_reviewers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            before = tmppath / "before.json"
            after = tmppath / "after.json"

            before.write_text("[]")
            after.write_text(
                json.dumps(
                    [
                        {"id": 12, "user": {"login": "someone-else"}},
                    ]
                )
            )

            ok, message = verify_review_output(
                "lambdaphus[bot]",
                "pr_comment",
                before,
                after,
            )

            assert ok is False
            assert message == "Review mode completed without posting a new review."
