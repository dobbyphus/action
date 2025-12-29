# Agent Request

@{{ author }} mentioned you in {{ repository }} #{{ number }}.

## Context

- **Context Type**: {{ context_type }}
- **Default Branch**: {{ default_branch }}

## User's Request

{{ comment }}

{{ inline_context }}

---

## Instructions

1. **Gather context first:**
   ```bash
   gh issue view {{ number }} --json title,body,state,labels,pullRequest
   ```

2. **Acknowledge immediately:**
   ```bash
   gh issue comment {{ number }} --body "$(cat <<'EOF'
   Hey @{{ author }}! I'm on it...
   EOF
   )"
   ```

3. **Plan your work** using todo tools.

4. **Investigate and satisfy the request.**

5. **If code changes are needed:**
   - **For PR comments** (`context_type` = `pr_comment`):
     You are already on the PR branch. Commit directly to the current branch.
   - **For issue comments or dispatch** (`context_type` = `issue_comment` or `dispatch`):
     Create a branch: `git checkout -b fix/issue-{{ number }}-short-description`

6. **NEVER run `git push`** - the action automatically handles pushing with
   signed commits after you're done. Just make your commits locally.

7. **NEVER run `gh pr create`** - the action automatically creates PRs when
   you push to a new branch.

8. **NEVER reference commit SHAs** in comments or reports - the SHAs change
   when commits are replayed as signed commits.

9. **Report completion** via comment on the issue/PR.
