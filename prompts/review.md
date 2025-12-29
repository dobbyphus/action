# PR Review

Review PR #{{ pr_number }}: {{ pr_title }}

## Context

- **Author**: @{{ pr_author }}
- **Requested by**: @{{ requested_by }}
- **Repository**: {{ repository }}

{{ inline_context }}

## Getting Started

```bash
gh pr view {{ pr_number }} --json files,reviewThreads,commits,additions,deletions
gh pr diff {{ pr_number }}
```

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

## Review Process

1. Fetch PR details with `gh pr view`
2. Read the diff with `gh pr diff`
3. Check for unresolved threads
4. Identify issues by severity: CRITICAL / WARNING / SUGGESTION
5. Submit review using `gh pr review`

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
