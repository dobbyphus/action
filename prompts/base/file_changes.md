## Git Workflow

### BLOCKING: Branch Verification (BEFORE ANY CODE CHANGES)

**Commits to the default branch (main/master) are REJECTED by the system.**

Before writing ANY code, editing ANY file, or making ANY commit:

```bash
# Check current branch
git branch --show-current
```

- If output is `main` or `master` → **STOP. Create a branch first.**
- If output is a feature branch → Proceed with changes.

### Required Workflow

1. **FIRST**: Create a branch (MANDATORY for any code changes):
   ```bash
   git checkout -b <branch-name>
   ```
   - For issues: `fix/issue-{{ number }}-short-description` or `feat/issue-{{ number }}-description`
   - General: `fix/typo-in-readme`, `feat/add-auth`

2. **VERIFY** you are on the new branch:
   ```bash
   git branch --show-current  # Must NOT be main/master
   ```

3. Make your changes and commit with clear messages

4. Your commits are automatically signed and pushed

5. A pull request is automatically created

### Why This Matters

The replay system WILL FAIL if you commit to the default branch. Your work will be lost. Always branch first.

### What You CAN Do

- `git checkout -b <branch>` - Create a branch (REQUIRED)
- `git add` - Stage files
- `git commit` - Create commits with meaningful messages
- Read, write, and edit files using your tools
- Use `gh` CLI for GitHub API operations (issues, comments)

### What You MUST NOT Do

- `git push` - NEVER push; the workflow handles this with signed commits
- `gh pr create` - NEVER create PRs; the workflow handles this automatically
- Commit directly to main/master - NEVER; always create a branch
- `git rebase -i` - NEVER rewrite history interactively
- Reference commit SHAs in comments - NEVER; SHAs change when replayed as signed

### Commit Messages

Use conventional commit format:

- `feat: add user authentication`
- `fix: resolve null pointer in parser`
- `docs: update API documentation`
- `refactor: simplify error handling`
