"""Tests for fetch_threads.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_threads import fetch_unresolved_threads, format_threads_for_prompt


class TestFetchUnresolvedThreads:
    """Tests for fetch_unresolved_threads function.

    Note: These tests mock the GraphQL response since actual API calls
    require authentication and a real PR.
    """

    def test_empty_response(self, monkeypatch):
        """Test handling of empty/None GraphQL response."""

        def mock_run_graphql(query, variables):
            return None

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert result == []

    def test_no_threads(self, monkeypatch):
        """Test PR with no review threads."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
                }
            }

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert result == []

    def test_all_resolved(self, monkeypatch):
        """Test PR where all threads are resolved."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "nodes": [
                                    {
                                        "id": "thread1",
                                        "isResolved": True,
                                        "path": "file.py",
                                        "line": 10,
                                        "startLine": None,
                                        "viewerCanResolve": True,
                                        "comments": {"nodes": []},
                                    }
                                ]
                            }
                        }
                    }
                }
            }

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert result == []

    def test_unresolved_threads(self, monkeypatch):
        """Test extraction of unresolved threads."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "nodes": [
                                    {
                                        "id": "thread1",
                                        "isResolved": False,
                                        "path": "src/main.py",
                                        "line": 42,
                                        "startLine": 40,
                                        "viewerCanResolve": True,
                                        "comments": {
                                            "nodes": [
                                                {
                                                    "id": "comment1",
                                                    "databaseId": 12345,
                                                    "author": {"login": "reviewer"},
                                                    "body": "Fix this bug",
                                                    "createdAt": "2025-01-01T00:00:00Z",
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "id": "thread2",
                                        "isResolved": True,
                                        "path": "README.md",
                                        "line": 5,
                                        "startLine": None,
                                        "viewerCanResolve": True,
                                        "comments": {"nodes": []},
                                    },
                                ]
                            }
                        }
                    }
                }
            }

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert len(result) == 1
        assert result[0]["id"] == "thread1"
        assert result[0]["path"] == "src/main.py"
        assert result[0]["line"] == 42
        assert result[0]["start_line"] == 40
        assert result[0]["can_resolve"] is True
        assert len(result[0]["comments"]) == 1
        assert result[0]["comments"][0]["author"] == "reviewer"
        assert result[0]["comments"][0]["body"] == "Fix this bug"

    def test_malformed_response(self, monkeypatch):
        """Test handling of malformed GraphQL response."""

        def mock_run_graphql(query, variables):
            return {"data": {"repository": None}}

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert result == []

    def test_null_thread_in_nodes(self, monkeypatch):
        """Test handling of null thread in nodes array."""

        def mock_run_graphql(query, variables):
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "nodes": [
                                    None,
                                    {
                                        "id": "thread1",
                                        "isResolved": False,
                                        "path": "file.py",
                                        "line": 10,
                                        "startLine": None,
                                        "viewerCanResolve": False,
                                        "comments": {"nodes": []},
                                    },
                                ]
                            }
                        }
                    }
                }
            }

        monkeypatch.setattr("fetch_threads.run_graphql", mock_run_graphql)

        result = fetch_unresolved_threads("owner", "repo", 1)
        assert len(result) == 1
        assert result[0]["id"] == "thread1"


class TestFormatThreadsForPrompt:
    """Tests for format_threads_for_prompt function."""

    def test_empty_threads(self):
        """Test formatting with no threads."""
        result = format_threads_for_prompt([])
        assert result == "No unresolved review threads."

    def test_single_thread(self):
        """Test formatting a single thread."""
        threads = [
            {
                "id": "thread123",
                "path": "src/main.py",
                "line": 42,
                "start_line": None,
                "can_resolve": True,
                "comments": [
                    {
                        "author": "reviewer",
                        "body": "Please fix this",
                    }
                ],
            }
        ]

        result = format_threads_for_prompt(threads)
        assert "1 unresolved review thread" in result
        assert "src/main.py:42" in result
        assert "thread123" in result
        assert "@reviewer" in result
        assert "Please fix this" in result

    def test_multiline_thread(self):
        """Test formatting thread with start and end lines."""
        threads = [
            {
                "id": "thread123",
                "path": "src/main.py",
                "line": 50,
                "start_line": 45,
                "can_resolve": True,
                "comments": [],
            }
        ]

        result = format_threads_for_prompt(threads)
        assert "src/main.py:45-50" in result

    def test_long_comment_truncation(self):
        """Test that long comments are truncated."""
        long_body = "x" * 300
        threads = [
            {
                "id": "thread123",
                "path": "file.py",
                "line": 10,
                "start_line": None,
                "can_resolve": False,
                "comments": [{"author": "user", "body": long_body}],
            }
        ]

        result = format_threads_for_prompt(threads)
        assert "..." in result
        assert len(result) < len(long_body) + 500  # Reasonable truncation

    def test_multiple_threads(self):
        """Test formatting multiple threads."""
        threads = [
            {
                "id": "thread1",
                "path": "file1.py",
                "line": 10,
                "start_line": None,
                "can_resolve": True,
                "comments": [],
            },
            {
                "id": "thread2",
                "path": "file2.py",
                "line": 20,
                "start_line": None,
                "can_resolve": False,
                "comments": [],
            },
        ]

        result = format_threads_for_prompt(threads)
        assert "2 unresolved review thread" in result
        assert "Thread 1" in result
        assert "Thread 2" in result
        assert "file1.py" in result
        assert "file2.py" in result
