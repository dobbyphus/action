## GitHub Comment Formatting

### ALWAYS use heredoc syntax for comments containing code references, backticks, or multiline content:

If unsure, default to heredoc to avoid shell escaping issues. Never risk backtick loss.

```bash
gh issue comment <number> --body "$(cat <<'EOF'
Your comment with `backticks` and code references preserved here.
Multiple lines work perfectly.
EOF
)"
```

### NEVER use direct quotes with backticks (shell will interpret them as command substitution):

```bash
# WRONG - backticks disappear:
gh issue comment 123 --body "text with `code`"

# CORRECT - backticks preserved:
gh issue comment 123 --body "$(cat <<'EOF'
text with `code`
EOF
)"
```

### GitHub Markdown Rules (MUST FOLLOW)

**Code blocks MUST use EXACTLY 3 backticks and a language identifier.**
- CORRECT: ` ```bash ` ... ` ``` `
- WRONG: ` ``` ` (no language), ` ```` ` (4 backticks), ` `` ` (2 backticks)

**Close every fence on its own line.**

**Do not add trailing backticks or spaces after the closing fence.**

**Use SINGLE backticks for inline code:** `code` not ```code```

**Do not use lists inside fenced code blocks.**
