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

### INFRASTRUCTURE / ANSIBLE REVIEW CHECKS

When reviewing infrastructure-as-code, Ansible, Kubernetes, Terraform, or
deployment automation changes, do not stop at syntax and lint checks. Look for
contextual regressions created by tags, conditionals, inventory variables, and
runtime ordering.

For Ansible playbooks and roles specifically:

- Check changed service names against existing variables/defaults/group_vars.
  A hard-coded service is a blocker when the repo already has a conditional
  variant, for example kubelet-container vs classic systemd services.
- Check tag semantics for `never`, `--tags`, `import_role`, `include_role`, and
  `apply.tags`. If a PR advertises a tag as an entry point, verify the tag
  selects every prerequisite task it needs.
- If the PR claims a tagged Ansible entry point works but does not include
  evidence, flag the missing validation and name the exact validation command
  the author should run, for example `ansible-playbook ... --tags <tag>
  --list-tasks`.
- Treat `failed_when: false`, `ignore_errors`, and broad shell hooks around
  service restarts as suspicious. They are blockers when they can hide failed
  restarts, stale certificates, or partially-applied runtime state.
- Cross-check new reusable task files from both call sites: normal role flow
  and explicit tagged entry points.
- If a Copilot/human finding is partly wrong, still look for the underlying
  real defect. Fix the real defect; do not blindly apply the suggested patch.

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
