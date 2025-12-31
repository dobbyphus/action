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
# 2. Reply explaining what you fixed
#    - Single mode: use {{ comment_id }}
#    - Batch mode: use the Comment ID from the thread data above
gh api repos/{{ repository }}/pulls/{{ pr_number }}/comments/COMMENT_ID/replies \
  -X POST \
  -f body="$(cat <<'EOF'
Fixed! [Explain what you changed and why]
EOF
)"

# 3. Resolve the thread (use the Thread ID from the thread data, looks like PRRT_...)
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
#    - Single mode: use {{ comment_id }}
#    - Batch mode: use the Comment ID from the thread data above
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
#    - Single mode: use {{ comment_id }}
#    - Batch mode: use the Comment ID from the thread data above
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

1. **Comment IDs**:
   - **Single Comment Mode**: Use `{{ comment_id }}` directly in the commands (it's already known)
   - **Batch Mode**: Get the Comment ID from each thread's data in "Unresolved Review Threads" above
   - Example: If thread shows `**Comment ID**: \`2654335644\``, use that number

2. **Thread IDs (for GraphQL)**:
   - The GraphQL `resolveReviewThread` mutation requires the GraphQL node ID
   - Find it in the thread data as `**Thread ID**: \`PRRT_...\``
   - Example: `PRRT_kwDOxxxxxxx...`

3. **Only Resolve When Fixed**: Never resolve a thread unless you've actually made
   the code change. If you disagree or need clarification, leave the thread open.

4. **Lockstep = Sequential**: Complete each comment fully (analyze → act → resolve)
   before moving to the next.

5. **Batch Summary**: When completing batch mode, post a summary comment:
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
