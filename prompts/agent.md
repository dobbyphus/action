# Agent Request

Work requested in {{ repository }}.

## Context

- **Context Type**: {{ context_type }}
- **Target**: {{ number }}
- **Default Branch**: {{ default_branch }}
- **Requested by**: {{ author }}

## User's Request

{{ comment }}

{{ inline_context }}

---

## Instructions

### For `dispatch` (workflow_dispatch with no target)

1. **DO NOT comment on any issue or PR** - there is no target.
2. **Plan your work** using todo tools.
3. **Investigate and satisfy the request** silently.
4. **If you need to report findings**, create a NEW issue:
   ```bash
   gh issue create --title "Title" --body "Body"
   ```
5. **If code changes are needed**, create a branch:
   ```bash
   git checkout -b feat/short-description
   ```

### For `pr_inline_comment` (inline diff comments)

When responding to inline diff comments, reply **in the thread** (not the main PR).

**Determine your mode:**
- If the comment asks you to handle "all", "each", or "every" comment → **Batch Mode**
- Otherwise → **Single Comment Mode** (handle only the triggering comment)

{{ base_review_threads }}

#### Single Comment Mode Workflow

1. **Gather context first:**
   ```bash
   gh pr view {{ number }} --json title,body,state,labels
   ```

2. **Acknowledge immediately** (reply to the thread):
   ```bash
   gh api repos/{{ repository }}/pulls/{{ number }}/comments/{{ comment_id }}/replies \
     -X POST \
     -f body="$(cat <<'EOF'
   {{ author_mention }} I'm on it...
   EOF
   )"
   ```

3. **Plan your work** using todo tools.

4. **Investigate and satisfy the request.**

5. **If code changes are needed:**
   You are already on the PR branch. Commit directly to the current branch.

6. **Report completion and resolve if fixed** (reply to the thread):
   ```bash
   # Reply explaining what you did
   gh api repos/{{ repository }}/pulls/{{ number }}/comments/{{ comment_id }}/replies \
     -X POST \
     -f body="$(cat <<'EOF'
   Done! Here's what I did...
   EOF
   )"

   # If you FIXED the issue, resolve the thread (use GraphQL thread ID from unresolved_threads)
   gh api graphql -f query='
     mutation {
       resolveReviewThread(input: {pullRequestReviewThreadId: "THREAD_ID"}) {
         thread { isResolved }
       }
     }
   '
   ```

#### Batch Mode Workflow

When handling ALL unresolved threads:

1. **Acknowledge** on the main PR:
   ```bash
   gh pr comment {{ number }} --body "$(cat <<'EOF'
   {{ author_mention }} I'll address all {{ unresolved_threads_count }} unresolved review comments.
   EOF
   )"
   ```

2. **Process each thread** using the lockstep workflow above (see `{{ base_review_threads }}`).

3. **Post summary** after completing all threads:
   ```bash
   gh pr comment {{ number }} --body "$(cat <<'EOF'
   ## Review Comments Addressed

   | Thread | File | Action | Status |
   |--------|------|--------|--------|
   | ... | ... | ... | ... |

   [Summary of changes made]
   EOF
   )"
   ```

### For `issue_comment`, `pr_comment`

1. **Gather context first:**
   ```bash
   gh issue view {{ number }} --json title,body,state,labels,comments
   ```

2. **Acknowledge immediately:**
   ```bash
   gh issue comment {{ number }} --body "$(cat <<'EOF'
   {{ author_mention }} I'm on it...
   EOF
   )"
   ```

3. **Plan your work** using todo tools.

4. **Investigate and satisfy the request.**

5. **If code changes are needed:**
   - **For PR comments** (`context_type` = `pr_comment`):
     You are already on the PR branch. Commit directly to the current branch.
   - **For issue comments** (`context_type` = `issue_comment`):
     Create a branch: `git checkout -b fix/issue-{{ number }}-short-description`

6. **Report completion** via comment on #{{ number }}.

---

## Global Rules

- **NEVER run `git push`** - the action automatically handles pushing with
  signed commits after you're done. Just make your commits locally.

- **NEVER run `gh pr create`** - the action automatically creates PRs when
  you push to a new branch.

- **NEVER reference commit SHAs** in comments or reports - the SHAs change
  when commits are replayed as signed commits.

- **NEVER comment on unrelated issues/PRs** - only interact with #{{ number }}
  (or create new issues if reporting findings from dispatch).
