## Commit Message Style (Linux Kernel Style)

Follow Linux kernel commit message conventions for all commits.

### Subject Line

- **50 characters maximum** - this is a hard limit, not a suggestion
  - Exceptional cases (e.g., long function names): 72 chars absolute max
  - If you can't fit in 50, your subject is too detailed - move detail to body
- **Imperative mood**: "Add feature" not "Added feature" or "Adds feature"
- **Format**: `subsystem: summary phrase` or `type(scope): summary`
  - Subsystem examples: `prompts`, `scripts`, `action`, `ci`
  - Type examples: `fix`, `feat`, `chore`, `refactor`, `test`, `docs`
- **No period** at end
- **Specific and descriptive**: the subject becomes a globally-unique identifier

Good examples:
- `scripts: add retry logic to API calls` (36 chars)
- `fix(prompts): clarify branch requirements` (41 chars)
- `prompts: add research mode classification` (41 chars)

Bad examples:
- `update files` (too vague)
- `Fixed the bug.` (wrong mood, has period)
- `feat: add feature to do the thing that was requested` (too long - 52 chars)
- `fix(prompts): clarify branch creation requirements` (50 chars - at limit, prefer shorter)

### Body

- **Blank line** separating subject from body (mandatory)
- **Wrap at 72 characters** per line
- **Explain what AND why**, not how (the code shows how)
- **Use prose paragraphs**, not bullet points
- Describe: the problem, your solution, why this approach

Structure your explanation as a narrative:
1. What was the problem or motivation?
2. What does this change do about it?
3. Why is this the right approach?

### Example

```
prompts: add intent classification for research vs implementation

Agent previously treated all requests as implementation tasks, leading
to unwanted code changes when users only wanted investigation. The
"research this issue" command resulted in commits that were rejected
because no branch was created.

Add explicit intent classification section that distinguishes RESEARCH
mode (investigate and report) from IMPLEMENTATION mode (create branch
and code). Include trigger word lists and clear examples to guide the
agent's behavior.

Closes #42
```

### Trailers (Optional)

Place at the end of the body, after a blank line:
- `Fixes: <sha> ("subject")` - links to the commit that introduced a bug
- `Closes: <url>` - closes an issue/PR when merged
- `Refs: #123` - references related issues without closing

### Anti-patterns (NEVER do these)

- Generic subjects: "fix bug", "update code", "changes"
- Bullet-point bodies instead of prose
- Describing what the diff shows (reader can see the diff)
- Extremely long subjects that get truncated
- Missing blank line between subject and body
