# PR Review

Review PR #{{ pr_number }}: {{ pr_title }}

## Context

- **Author**: {{ pr_author }}
- **Requested by**: {{ requested_by }}
- **Repository**: {{ repository }}
- **Context Type**: {{ context_type }}

{{ inline_context }}

## Required First Steps (NON-NEGOTIABLE)

1. **READ FULL PR CONTEXT** (all comments and reviews) BEFORE ANY REVIEW ACTION:
   ```bash
   gh pr view {{ pr_number }} --comments
   gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments
   gh api repos/{{ repository }}/pulls/{{ pr_number }}/reviews
   ```
2. Capture prior decisions, feedback, and unresolved concerns before reviewing.
3. **CREATE TODOS IMMEDIATELY AFTER READING** using todo tools.
4. If you post any interim comment, include requirements + TODOs explicitly.

## Getting Started

```bash
gh pr view {{ pr_number }} --json files,reviews,commits,additions,deletions
gh pr diff {{ pr_number }}
```

## Responding to Inline Comments

When `context_type` is `pr_inline_comment`, you MUST reply in the same thread
using the GitHub API (NOT `gh issue comment` or `gh pr review`):

```bash
gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments \
  -X POST \
  -f body="$(cat <<'EOF'
Your reply here
EOF
)" \
  -F in_reply_to={{ comment_id }}
```

This ensures your response appears in the correct inline thread, not as a
separate PR comment.

## Review Guidelines

### CRITICAL (must fix)

- Security vulnerabilities (hardcoded secrets, SQL injection, XSS)
- Breaking changes without migration
- Type safety violations (`as any`, `@ts-ignore`)
- Missing error handling

### CODE QUALITY

- Follows existing codebase patterns
- No excessive comments
- Tests for new functionality

### Output Requirements (NON-NEGOTIABLE)

- Label every finding as `BLOCKER` or `NON-BLOCKER`.
- Anchor every finding to an exact `file:line` (or exact symbol name if no line).
- Do not use `might`, `could`, `maybe`, or `consider`.
- Never state or imply you ran commands you did not run.

## Review Process

1. Fetch PR details with `gh pr view`.
2. Read the diff with `gh pr diff`.
3. Check for unresolved threads.
4. Identify issues by severity: CRITICAL / WARNING / SUGGESTION.
5. Submit review using `gh pr review`.

**Note**: This is a review-only task. NEVER make commits, run `git push`, or
reference commit SHAs (they change when replayed as signed commits).

## Output

```bash
gh pr review {{ pr_number }} --comment --body "$(cat <<'EOF'
## Code Review

### Summary
[1-2 sentence overview]

### Issues Found
[List issues with severity, or "No issues found"]

### Verdict
[APPROVE / REQUEST_CHANGES / COMMENT]
EOF
)"
```

Use `--request-changes` or `--approve` instead of `--comment` as appropriate.
