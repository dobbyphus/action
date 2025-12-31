"""Tests for resolve_thread.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from resolve_thread import resolve_thread, unresolve_thread


class TestResolveThread:
    """Tests for resolve_thread function."""

    def test_successful_resolve(self, monkeypatch):
        """Test successful thread resolution."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "resolveReviewThread": {
                        "thread": {"id": "thread123", "isResolved": True}
                    }
                }
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = resolve_thread("thread123")
        assert result is True

    def test_failed_resolve_null_response(self, monkeypatch):
        """Test failed resolution with null response."""

        def mock_run_graphql(query, variables):
            return None

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = resolve_thread("thread123")
        assert result is False

    def test_failed_resolve_graphql_error(self, monkeypatch):
        """Test failed resolution with GraphQL error."""

        def mock_run_graphql(query, variables):
            return {
                "errors": [{"message": "Thread not found"}],
                "data": {"resolveReviewThread": None},
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = resolve_thread("thread123")
        assert result is False

    def test_failed_resolve_malformed_response(self, monkeypatch):
        """Test failed resolution with malformed response."""

        def mock_run_graphql(query, variables):
            return {"data": {}}

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = resolve_thread("thread123")
        assert result is False

    def test_resolve_not_resolved(self, monkeypatch):
        """Test when resolve returns isResolved=False."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "resolveReviewThread": {
                        "thread": {"id": "thread123", "isResolved": False}
                    }
                }
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = resolve_thread("thread123")
        assert result is False


class TestUnresolveThread:
    """Tests for unresolve_thread function."""

    def test_successful_unresolve(self, monkeypatch):
        """Test successful thread unresolve."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "unresolveReviewThread": {
                        "thread": {"id": "thread123", "isResolved": False}
                    }
                }
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = unresolve_thread("thread123")
        assert result is True

    def test_failed_unresolve_null_response(self, monkeypatch):
        """Test failed unresolve with null response."""

        def mock_run_graphql(query, variables):
            return None

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = unresolve_thread("thread123")
        assert result is False

    def test_failed_unresolve_still_resolved(self, monkeypatch):
        """Test when unresolve returns isResolved=True (still resolved)."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "unresolveReviewThread": {
                        "thread": {"id": "thread123", "isResolved": True}
                    }
                }
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = unresolve_thread("thread123")
        assert result is False

    def test_failed_unresolve_graphql_error(self, monkeypatch):
        """Test failed unresolve with GraphQL error."""

        def mock_run_graphql(query, variables):
            return {
                "errors": [{"message": "Permission denied"}],
                "data": {"unresolveReviewThread": None},
            }

        monkeypatch.setattr("resolve_thread.run_graphql", mock_run_graphql)

        result = unresolve_thread("thread123")
        assert result is False
