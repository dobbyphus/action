#!/usr/bin/env python3
"""Replay commits as signed via GitHub API and create PR if needed."""

import base64
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


def run(cmd: list[str], *, check: bool = True, capture: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=capture, text=True, check=check)
    return result.stdout.strip() if capture else ""


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check)


def gh_api(
    endpoint: str,
    *,
    method: str = "GET",
    input_data: dict | None = None,
    jq: str | None = None,
    check: bool = True,
) -> str:
    cmd = ["gh", "api", endpoint]
    if method != "GET":
        cmd.extend(["-X", method])
    if jq:
        cmd.extend(["--jq", jq])

    if input_data is not None:
        cmd.extend(["--input", "-"])
        result = subprocess.run(
            cmd,
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"gh api error: {result.stderr}", file=sys.stderr)
            if check:
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
        return result.stdout.strip()

    return run(cmd, check=check)


@dataclass
class Config:
    repo: str
    start_sha: str
    start_branch: str
    current_branch: str
    default_branch: str
    issue_number: str
    issue_title: str


def get_current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD")


def get_default_branch(repo: str) -> str:
    return gh_api(f"repos/{repo}", jq=".default_branch")


def get_issue_title(repo: str, number: str) -> str:
    if not number:
        return ""
    try:
        return gh_api(f"repos/{repo}/issues/{number}", jq=".title")
    except subprocess.CalledProcessError:
        return ""


def branch_exists_on_remote(repo: str, branch: str) -> bool:
    result = gh_api(
        f"repos/{repo}/git/refs/heads/{branch}",
        check=False,
    )
    if not result:
        return False
    try:
        data = json.loads(result)
        return "ref" in data
    except json.JSONDecodeError:
        return False


def get_remote_branch_sha(repo: str, branch: str) -> str | None:
    """Get the SHA of a branch on remote, or None if it doesn't exist."""
    result = gh_api(
        f"repos/{repo}/git/refs/heads/{branch}",
        jq=".object.sha",
        check=False,
    )
    # Check if we got a valid SHA (40 hex chars)
    if result and len(result) == 40:
        return result
    return None


def filter_new_commits(commits: list[str], remote_ref: str) -> list[str]:
    """Filter out commits that are ancestors of remote_ref (already on remote)."""
    new_commits = []
    for sha in commits:
        try:
            # If this succeeds, sha is an ancestor of remote_ref (already on remote)
            git("merge-base", "--is-ancestor", sha, remote_ref)
            print(f"  Skipping {sha[:7]} (already on remote)")
        except subprocess.CalledProcessError:
            # sha is NOT an ancestor of remote_ref (new commit)
            new_commits.append(sha)
    return new_commits


def get_commits(start_sha: str) -> list[str]:
    try:
        output = git("rev-list", "--reverse", f"{start_sha}..HEAD")
        return output.split() if output else []
    except subprocess.CalledProcessError:
        return []


def get_commit_message(sha: str) -> str:
    return git("log", "-1", "--format=%B", sha)


def get_commit_subject(sha: str) -> str:
    return git("log", "-1", "--format=%s", sha)


def get_changed_files() -> list[str]:
    output = git("diff", "--cached", "--name-only")
    return [f for f in output.split("\n") if f]


def create_blob(repo: str, file_path: str) -> str | None:
    path = Path(file_path)
    if not path.exists():
        return None
    content = base64.b64encode(path.read_bytes()).decode("ascii")
    response = gh_api(
        f"repos/{repo}/git/blobs",
        method="POST",
        input_data={"content": content, "encoding": "base64"},
    )
    return json.loads(response)["sha"]


def get_file_mode(file_path: str) -> str:
    path = Path(file_path)
    if path.exists() and os.access(path, os.X_OK):
        return "100755"
    return "100644"


def create_tree(repo: str, parent_sha: str, files: list[str]) -> str:
    parent_tree = gh_api(f"repos/{repo}/git/commits/{parent_sha}", jq=".tree.sha")

    tree_entries: list[dict] = []
    for file_path in files:
        blob_sha = create_blob(repo, file_path)
        entry: dict = {
            "path": file_path,
            "mode": get_file_mode(file_path),
            "type": "blob",
            "sha": blob_sha,
        }
        if blob_sha:
            print(f"    + {file_path}")
        else:
            print(f"    - {file_path} (deleted)")
        tree_entries.append(entry)

    response = gh_api(
        f"repos/{repo}/git/trees",
        method="POST",
        input_data={"base_tree": parent_tree, "tree": tree_entries},
    )
    return json.loads(response)["sha"]


def create_commit(repo: str, message: str, tree_sha: str, parent_sha: str) -> str:
    response = gh_api(
        f"repos/{repo}/git/commits",
        method="POST",
        input_data={"message": message, "tree": tree_sha, "parents": [parent_sha]},
    )
    return json.loads(response)["sha"]


def create_ref(repo: str, branch: str, sha: str) -> None:
    gh_api(
        f"repos/{repo}/git/refs",
        method="POST",
        input_data={"ref": f"refs/heads/{branch}", "sha": sha},
    )


def update_ref(repo: str, branch: str, sha: str) -> None:
    gh_api(
        f"repos/{repo}/git/refs/heads/{branch}",
        method="PATCH",
        input_data={"sha": sha, "force": True},
    )


def replay_commit(repo: str, original_sha: str, parent_sha: str) -> str | None:
    message = get_commit_message(original_sha)
    subject = get_commit_subject(original_sha)
    print(f"\n==> {subject}")

    try:
        git("cherry-pick", "-n", original_sha)
    except subprocess.CalledProcessError:
        print("    Cherry-pick failed, skipping")
        git("reset", "--hard", "HEAD")
        return None

    files = get_changed_files()
    if not files:
        print("    No file changes, skipping")
        return None

    tree_sha = create_tree(repo, parent_sha, files)
    commit_sha = create_commit(repo, message, tree_sha, parent_sha)
    print(f"    Signed: {commit_sha[:7]}")

    git("fetch", "origin", commit_sha, check=False)
    git("reset", "--hard", commit_sha)

    return commit_sha


def get_commit_body(sha: str) -> str:
    """Get the commit body (message without subject line)."""
    return git("log", "-1", "--format=%b", sha).strip()


def generate_pr_content_with_ai(commits: list[str], config: Config) -> tuple[str, str]:
    """Use opencode to generate PR title and body from multiple commits."""
    commit_info = []
    for sha in commits:
        subject = get_commit_subject(sha)
        body = get_commit_body(sha)
        commit_info.append(f"- {subject}")
        if body:
            commit_info.append(f"  {body}")

    commits_text = "\n".join(commit_info)

    issue_context = ""
    if config.issue_number:
        issue_context = f"\nThis PR addresses issue #{config.issue_number}"
        if config.issue_title:
            issue_context += f": {config.issue_title}"

    with (
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as title_file,
        tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as body_file,
    ):
        title_path = title_file.name
        body_path = body_file.name

    prompt = f"""Generate a pull request title and body for the following commits.
{issue_context}

Commits:
{commits_text}

INSTRUCTIONS:
1. Write ONLY the PR title to: {title_path}
   - Use conventional commit style (feat:, fix:, docs:, refactor:, etc.)
   - Maximum 50-60 characters
   - Be concise and descriptive
   - Do NOT include any newlines or extra text

2. Write the PR body to: {body_path}
   - Start with a brief summary (1-2 sentences)
   - Include a bullet list of changes
   - If there's an issue number, include "Closes #N" or "Fixes #N"
   - Use markdown formatting

Write ONLY to these files. Do not output anything else."""

    try:
        subprocess.run(
            ["opencode", "run", prompt],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        title = Path(title_path).read_text().strip()
        body = Path(body_path).read_text().strip()

        # Validate title length
        if len(title) > 72:
            title = title[:69] + "..."

        return title, body

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        # Fallback if opencode fails
        return generate_fallback_pr_content(commits, config)
    finally:
        # Clean up temp files
        for path in [title_path, body_path]:
            try:
                Path(path).unlink()
            except OSError:
                pass


def generate_fallback_pr_content(commits: list[str], config: Config) -> tuple[str, str]:
    """Generate PR content without AI (fallback)."""
    if config.issue_number and config.issue_title:
        title = config.issue_title
    elif commits:
        title = get_commit_subject(commits[0])
    else:
        title = f"Changes from {config.current_branch}"

    body_parts = []
    if len(commits) > 1:
        body_parts.append("## Changes\n")
        for sha in commits:
            subject = get_commit_subject(sha)
            body_parts.append(f"- {subject}")
        body_parts.append("")

    if config.issue_number:
        body_parts.append(f"Closes #{config.issue_number}")

    return title, "\n".join(body_parts)


def create_pull_request(config: Config, head_sha: str) -> str:
    commits = get_commits(config.start_sha)

    if len(commits) == 1:
        # Single commit: use its title and body directly
        title = get_commit_subject(commits[0])
        body = get_commit_body(commits[0])
        if config.issue_number:
            if body:
                body += f"\n\nCloses #{config.issue_number}"
            else:
                body = f"Closes #{config.issue_number}"
    elif len(commits) > 1:
        # Multiple commits: use AI to generate PR title and body
        print("Generating PR title and body from commits...")
        title, body = generate_pr_content_with_ai(commits, config)
    else:
        # No commits (shouldn't happen, but handle gracefully)
        title = f"Changes from {config.current_branch}"
        body = ""
        if config.issue_number:
            body = f"Closes #{config.issue_number}"

    response = gh_api(
        f"repos/{config.repo}/pulls",
        method="POST",
        input_data={
            "title": title,
            "body": body,
            "head": config.current_branch,
            "base": config.default_branch,
        },
    )
    data = json.loads(response)
    return data["html_url"]


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: replay_commits.py <start_sha> <start_branch> [issue_number]",
            file=sys.stderr,
        )
        return 1

    start_sha = sys.argv[1]
    start_branch = sys.argv[2]
    issue_number = sys.argv[3] if len(sys.argv) > 3 else ""

    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY not set", file=sys.stderr)
        return 1

    current_branch = get_current_branch()
    default_branch = get_default_branch(repo)
    issue_title = get_issue_title(repo, issue_number) if issue_number else ""

    config = Config(
        repo=repo,
        start_sha=start_sha,
        start_branch=start_branch,
        current_branch=current_branch,
        default_branch=default_branch,
        issue_number=issue_number,
        issue_title=issue_title,
    )

    print(f"Current branch: {current_branch}")
    print(f"Start branch: {start_branch}")
    print(f"Default branch: {default_branch}")

    commits = get_commits(start_sha)
    if not commits:
        print("\nNo commits to replay")
        return 0

    if current_branch == default_branch:
        print(
            f"\nError: Cannot replay commits to default branch '{default_branch}'",
            file=sys.stderr,
        )
        print("Agent must create a branch for changes.", file=sys.stderr)
        return 1

    remote_sha = get_remote_branch_sha(repo, current_branch)
    if remote_sha:
        print(f"Remote branch exists at {remote_sha[:7]}")
        git("fetch", "origin", current_branch, check=False)
        commits = filter_new_commits(commits, f"origin/{current_branch}")
        replay_base = remote_sha
    else:
        replay_base = start_sha

    if not commits:
        print("\nNo new commits to replay")
        return 0

    count = len(commits)
    print(f"\nReplaying {count} commit(s) as signed...")

    git("reset", "--hard", replay_base)
    parent_sha = replay_base

    for original_sha in commits:
        new_sha = replay_commit(repo, original_sha, parent_sha)
        if new_sha:
            parent_sha = new_sha

    is_new_branch = not branch_exists_on_remote(repo, current_branch)

    if is_new_branch:
        print(f"\nCreating ref {current_branch} -> {parent_sha[:7]}")
        create_ref(repo, current_branch, parent_sha)
    else:
        print(f"\nUpdating ref {current_branch} -> {parent_sha[:7]}")
        update_ref(repo, current_branch, parent_sha)

    print(f"Done! Replayed {count} commit(s) as signed.")

    if is_new_branch:
        print("\nCreating pull request...")
        pr_url = create_pull_request(config, parent_sha)
        print(f"PR created: {pr_url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
