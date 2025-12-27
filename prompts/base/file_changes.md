## Git Workflow

You MUST create a branch for your work. Commits to the default branch are not allowed.

### Required Workflow

1. Create a branch: `git checkout -b <branch-name>`
   - Use descriptive names: `fix/typo-in-readme`, `feat/add-auth`, `issue-42-fix-login`
2. Make your changes and commit with clear messages
3. Your commits are automatically signed and pushed
4. A pull request is automatically created

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
