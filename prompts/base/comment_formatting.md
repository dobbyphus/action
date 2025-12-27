## GitHub Comment Formatting

### ALWAYS use heredoc syntax for comments containing code references, backticks, or multiline content:

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

**Code blocks MUST have EXACTLY 3 backticks and language identifier:**
- CORRECT: ` ```bash ` ... ` ``` `
- WRONG: ` ``` ` (no language), ` ```` ` (4 backticks), ` `` ` (2 backticks)

**Every opening ` ``` ` MUST have a closing ` ``` ` on its own line**

**NO trailing backticks or spaces after closing ` ``` `**

**For inline code, use SINGLE backticks:** `code` not ```code```

**Lists inside code blocks break rendering - avoid them or use plain text**
