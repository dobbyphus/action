#!/usr/bin/env python3
"""Resolve a review thread via GraphQL mutation."""

import json
import subprocess
import sys


RESOLVE_MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: { pullRequestReviewThreadId: $threadId }) {
    thread {
      id
      isResolved
    }
  }
}
"""

UNRESOLVE_MUTATION = """
mutation($threadId: ID!) {
  unresolveReviewThread(input: { pullRequestReviewThreadId: $threadId }) {
    thread {
      id
      isResolved
    }
  }
}
"""


def run_graphql(query: str, variables: dict) -> dict | None:
    """Execute a GraphQL query/mutation via gh api."""
    cmd = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={query}",
    ]

    for key, value in variables.items():
        cmd.extend(["-f", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        print(f"GraphQL error: {result.stderr}", file=sys.stderr)
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse GraphQL response: {result.stdout}", file=sys.stderr)
        return None


def resolve_thread(thread_id: str) -> bool:
    """Resolve a review thread.

    Args:
        thread_id: The GraphQL node ID of the review thread

    Returns:
        True if successful, False otherwise
    """
    response = run_graphql(RESOLVE_MUTATION, {"threadId": thread_id})

    if not response:
        return False

    try:
        thread = response["data"]["resolveReviewThread"]["thread"]
        return thread.get("isResolved", False)
    except (KeyError, TypeError):
        # Check for errors in response
        errors = response.get("errors", [])
        if errors:
            for error in errors:
                print(f"GraphQL error: {error.get('message')}", file=sys.stderr)
        return False


def unresolve_thread(thread_id: str) -> bool:
    """Unresolve a review thread.

    Args:
        thread_id: The GraphQL node ID of the review thread

    Returns:
        True if successful, False otherwise
    """
    response = run_graphql(UNRESOLVE_MUTATION, {"threadId": thread_id})

    if not response:
        return False

    try:
        thread = response["data"]["unresolveReviewThread"]["thread"]
        return not thread.get("isResolved", True)
    except (KeyError, TypeError):
        errors = response.get("errors", [])
        if errors:
            for error in errors:
                print(f"GraphQL error: {error.get('message')}", file=sys.stderr)
        return False


def main() -> None:
    """Entry point - resolve or unresolve a thread."""
    if len(sys.argv) < 2:
        print(
            "Usage: resolve_thread.py <thread_id> [--unresolve]",
            file=sys.stderr,
        )
        sys.exit(1)

    thread_id = sys.argv[1]
    unresolve = "--unresolve" in sys.argv

    if unresolve:
        success = unresolve_thread(thread_id)
        action = "Unresolved"
    else:
        success = resolve_thread(thread_id)
        action = "Resolved"

    if success:
        print(f"{action} thread: {thread_id}")
    else:
        print(f"Failed to {action.lower()} thread: {thread_id}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
