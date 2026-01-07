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

## Intent Classification (DETERMINE FIRST)

Before taking any action, classify the request:

### RESEARCH Mode

**Trigger words**: "research", "investigate", "analyze", "look into", "review", "check", "explore", "understand", "explain", "examine", "assess", "evaluate", "diagnose"

**What to do**:
- Gather information and analyze
- Read code, issues, logs, documentation
- Report findings via comment on #{{ number }}
- **DO NOT write code, create branches, or make commits**

**Output**: A comment summarizing findings, root causes, recommendations

### IMPLEMENTATION Mode

**Trigger words**: "fix", "implement", "create", "add", "update", "change", "build", "make", "refactor", "migrate", "upgrade", "resolve", "address" (as in "address this bug")

**What to do**:
- **FIRST**: Create a branch (`git checkout -b <branch-name>`)
- Then: Write code, tests, make commits
- The workflow handles push and PR creation

**CRITICAL**: If IMPLEMENTATION mode, you MUST create a branch BEFORE any code changes.

### Mixed Requests

If a request contains BOTH research AND implementation language (e.g., "investigate and fix"):
- Default to **RESEARCH first**: understand the problem fully
- Ask for confirmation before implementing OR
- If clearly actionable, proceed to IMPLEMENTATION with branch creation

### When in Doubt

- "research this issue" → RESEARCH only
- "look into this and create a PR" → IMPLEMENTATION (explicit PR request)
- "investigate the bug" → RESEARCH only
- "fix the bug" → IMPLEMENTATION

---

## Instructions

### Required First Steps (NON-NEGOTIABLE)

1. **READ ALL RELEVANT CONTEXT BEFORE ANY ACTION**:
   - Issues: `gh issue view {{ number }} --comments`
   - PRs: `gh pr view {{ number }} --comments`, `gh api repos/{{ repository }}/pulls/{{ number }}/comments`, and `gh api repos/{{ repository }}/pulls/{{ number }}/reviews`
   - Extract: original request, prior attempts, decisions, rejections, and unresolved concerns.
2. **CREATE TODOS IMMEDIATELY AFTER READING** using todo tools.
   - First todo must summarize context and requirements.
   - Break work into atomic, verifiable steps.
3. **DO NOT ASK QUESTIONS.** Proceed with the best available context.

### TDD (MANDATORY IF TEST INFRA EXISTS)

1. Write requirements/spec.
2. Write tests (failing).
3. RED: confirm tests fail.
4. Implement minimal code.
5. GREEN: tests pass.
6. Refactor only if still green.
7. Repeat per feature.

### Completion Rules (ZERO TOLERANCE)

- **NO partial delivery**: no demos, skeletons, or subsets.
- **NO scope reduction**: do not drop requirements.
- **NO premature done**: do not report completion until ALL todos are complete and verified.
- **NO silent finishes**: the final report must include changes, verification steps, tests run (or why not), and remaining risks.
- **ONLY mark done after evidence**: show what you changed and how it was verified.
- **NO false execution claims**: never state or imply you ran commands you did not run.
- **BE DIRECT AND CONCISE**: remove filler, state only decisions, actions, and outcomes.

### Orchestration Guidelines (REQUIRED)

- Parallelize exploration (background agents + direct tools) when context is unclear.
- Synthesize findings before implementing. Re-read the user request before reporting.
- If a step fails twice, stop. Summarize failure signals, list hypotheses, pick the next diagnostic, and escalate strategy.
- If blocked by missing inputs, state the blocker and required inputs in one sentence.

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

2. **Acknowledge immediately** with requirements + TODOs (reply to the thread):
   ```bash
   gh api repos/{{ repository }}/pulls/{{ number }}/comments/{{ comment_id }}/replies \
     -X POST \
     -f body="$(cat <<'EOF'
   {{ author_mention }} I have read the full thread. Here's my understanding and plan:

   - Requirements: ...
   - TODOs: ...
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

1. **Classify intent** (see Intent Classification above):
   - RESEARCH → Investigate and report findings only
   - IMPLEMENTATION → Create branch, then code

2. **Gather context first:**
   ```bash
   gh issue view {{ number }} --json title,body,state,labels,comments
   ```

3. **Acknowledge immediately** with your classification + TODOs:
   ```bash
   gh issue comment {{ number }} --body "$(cat <<'EOF'
   {{ author_mention }} I have read the full thread. Here's my understanding and plan:

   - **Mode**: [RESEARCH / IMPLEMENTATION]
   - **Requirements**: ...
   - **TODOs**: ...
   EOF
   )"
   ```

4. **Plan your work** using todo tools.

5. **Execute based on mode:**

   **If RESEARCH mode:**
   - Investigate: read code, analyze, gather information
   - **DO NOT** write code, create branches, or make commits
   - Report findings via comment on #{{ number }}

   **If IMPLEMENTATION mode:**
   - **For PR comments** (`context_type` = `pr_comment`):
     You are already on the PR branch. Commit directly to the current branch.
   - **For issue comments** (`context_type` = `issue_comment`):
     **FIRST**: Create a branch before ANY code changes:
     ```bash
     git checkout -b fix/issue-{{ number }}-short-description
     git branch --show-current  # Verify NOT on main
     ```
   - Then: Make changes, write tests, commit

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
