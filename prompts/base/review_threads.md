## Handling Review Comments (Lockstep Workflow)

When working on PR review comments, follow this lockstep workflow for EACH comment.

### Determining Mode

**Single Comment Mode**: You were triggered by a specific inline comment mention.
- Work on ONLY the comment that triggered you
- The triggering comment is in `{{ inline_context }}`

**Batch Mode**: The user asked you to handle "all", "each", or "every" comment.
- Work on ALL unresolved threads listed below
- Process them one at a time in lockstep

### Unresolved Review Threads

{{ unresolved_threads }}

### Lockstep Workflow (Per Comment)

For EACH review comment, follow this exact sequence:

#### 1. Analyze the Comment

Determine if this is:
- **FIX**: You can address the comment with a code change
- **DISAGREE**: The suggestion is incorrect or not applicable
- **UNCLEAR**: You need clarification to proceed

#### 2. Take Action Based on Analysis

**If FIX:**

```bash
# 1. Make the code change (using your tools)
# 2. Reply explaining what you fixed (replace COMMENT_ID with the numeric comment ID)
gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments/COMMENT_ID/replies \
  -X POST \
  -f body="$(cat <<'EOF'
Fixed! [Explain what you changed and why]
EOF
)"

# 3. Resolve the thread (replace THREAD_ID with the GraphQL node ID like PRRT_...)
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {pullRequestReviewThreadId: "THREAD_ID"}) {
      thread { isResolved }
    }
  }
'
```

**If DISAGREE:**

```bash
# 1. Reply explaining why you disagree (DO NOT resolve)
# Replace COMMENT_ID with the numeric comment ID
gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments/COMMENT_ID/replies \
  -X POST \
  -f body="$(cat <<'EOF'
I respectfully disagree with this suggestion.

**Reason**: [Explain why the suggestion is incorrect or not applicable]
**Evidence**: [Reference code, documentation, or patterns that support your position]

I'll leave this thread open for discussion.
EOF
)"
```

**If UNCLEAR:**

```bash
# 1. Ask for clarification (DO NOT resolve)
# Replace COMMENT_ID with the numeric comment ID
gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments/COMMENT_ID/replies \
  -X POST \
  -f body="$(cat <<'EOF'
I need clarification on this comment.

**What's unclear**: [Explain what you don't understand]
**Why it matters**: [How clarification will help you proceed]
**Options I see**: [If applicable, list possible interpretations]

Once clarified, I can [describe what you'll be able to do].
EOF
)"
```

### Important Notes

1. **Placeholders to Replace**:
   - `COMMENT_ID`: The numeric database ID of the comment (e.g., `2654335644`)
   - `THREAD_ID`: The GraphQL node ID for the thread (looks like `PRRT_...`)
   - Both IDs are provided in the unresolved threads data above

2. **Thread ID vs Comment ID**: The GraphQL `resolveReviewThread` mutation requires
   the GraphQL node ID (looks like `PRRT_...`), while the REST API `/replies` endpoint
   uses the numeric comment ID in the URL path.

3. **Only Resolve When Fixed**: Never resolve a thread unless you've actually made
   the code change. If you disagree or need clarification, leave the thread open.

4. **Lockstep = Sequential**: Complete each comment fully (analyze → act → resolve)
   before moving to the next.

4. **Batch Summary**: When completing batch mode, post a summary comment:
   ```bash
   gh pr comment {{ pr_number }} --body "$(cat <<'EOF'
   ## Review Comments Addressed

   | Thread | File | Action | Status |
   |--------|------|--------|--------|
   | 1 | path/to/file.py:42 | Fixed | ✅ Resolved |
   | 2 | path/to/other.py:10 | Disagreed | ⚠️ Open for discussion |

   [Additional context if needed]
   EOF
   )"
   ```
