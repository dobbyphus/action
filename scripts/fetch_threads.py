#!/usr/bin/env python3
"""Fetch unresolved review threads from a pull request via GraphQL."""

import json
import os
import subprocess
import sys


QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        totalCount
        nodes {
          id
          isResolved
          path
          line
          startLine
          viewerCanResolve
          comments(first: 10) {
            totalCount
            nodes {
              id
              databaseId
              author {
                login
              }
              body
              createdAt
            }
          }
        }
      }
    }
  }
}
"""


def run_graphql(query: str, variables: dict) -> dict | None:
    """Execute a GraphQL query via gh api."""
    cmd = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={query}",
    ]

    for key, value in variables.items():
        if isinstance(value, int):
            cmd.extend(["-F", f"{key}={value}"])
        else:
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


def fetch_unresolved_threads(owner: str, repo: str, pr_number: int) -> list[dict]:
    """Fetch all unresolved review threads for a pull request.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number

    Returns:
        List of unresolved thread objects with their comments
    """
    variables = {"owner": owner, "repo": repo, "number": pr_number}
    response = run_graphql(QUERY, variables)

    if not response:
        return []

    try:
        review_threads = response["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads = review_threads["nodes"]
        total_threads = review_threads.get("totalCount", len(threads))
    except (KeyError, TypeError):
        return []

    # Warn if pagination limits might be truncating data
    if total_threads > 100:
        print(
            f"Warning: PR has {total_threads} review threads, but only fetching first 100",
            file=sys.stderr,
        )

    unresolved = []
    for thread in threads:
        if thread and not thread.get("isResolved", True):
            comments_data = thread.get("comments", {})
            comments_nodes = comments_data.get("nodes", [])
            comments_total = comments_data.get("totalCount", len(comments_nodes))

            # Warn if this thread has more comments than we fetched
            if comments_total > 10:
                print(
                    f"Warning: Thread {thread.get('id')} has {comments_total} "
                    "comments, but only fetching first 10",
                    file=sys.stderr,
                )

            unresolved.append(
                {
                    "id": thread.get("id"),
                    "path": thread.get("path"),
                    "line": thread.get("line"),
                    "start_line": thread.get("startLine"),
                    "can_resolve": thread.get("viewerCanResolve", False),
                    "comments": [
                        {
                            "id": c.get("id"),
                            "database_id": c.get("databaseId"),
                            "author": c.get("author", {}).get("login", "unknown"),
                            "body": c.get("body", ""),
                            "created_at": c.get("createdAt"),
                        }
                        for c in comments_nodes
                        if c
                    ],
                }
            )

    return unresolved


def format_threads_for_prompt(threads: list[dict]) -> str:
    """Format threads as a human-readable summary for the prompt.

    Args:
        threads: List of unresolved thread objects

    Returns:
        Formatted string summary of threads
    """
    if not threads:
        return "No unresolved review threads."

    lines = [f"Found {len(threads)} unresolved review thread(s):\n"]

    for i, thread in enumerate(threads, 1):
        path = thread.get("path", "unknown")
        line = thread.get("line")
        start_line = thread.get("start_line")

        if start_line and start_line != line:
            location = f"{path}:{start_line}-{line}"
        elif line:
            location = f"{path}:{line}"
        else:
            location = path

        lines.append(f"### Thread {i}: `{location}`")
        lines.append(f"- **Thread ID**: `{thread.get('id')}`")
        lines.append(f"- **Can Resolve**: {thread.get('can_resolve', False)}")

        comments = thread.get("comments", [])
        if comments:
            lines.append("- **Comments**:")
            for comment in comments:
                author = comment.get("author", "unknown")
                database_id = comment.get("database_id")
                body = comment.get("body", "").strip()
                # Truncate long comments in summary
                if len(body) > 200:
                    body = body[:197] + "..."
                lines.append(f"  - **Comment ID**: `{database_id}`")
                lines.append(f"  - @{author}: {body}")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Entry point - fetches threads and outputs JSON."""
    if len(sys.argv) < 4:
        print(
            "Usage: fetch_threads.py <owner> <repo> <pr_number>",
            file=sys.stderr,
        )
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    try:
        pr_number = int(sys.argv[3])
    except ValueError:
        print(f"Invalid PR number: {sys.argv[3]}", file=sys.stderr)
        sys.exit(1)

    threads = fetch_unresolved_threads(owner, repo, pr_number)

    # Output JSON for machine consumption
    result = {
        "threads": threads,
        "count": len(threads),
        "summary": format_threads_for_prompt(threads),
    }

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        import secrets

        eof_marker = secrets.token_hex(16)
        with open(github_output, "a") as f:
            f.write(f"json<<{eof_marker}\n")
            f.write(json.dumps(result))
            f.write(f"\n{eof_marker}\n")
            f.write(f"count={len(threads)}\n")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
