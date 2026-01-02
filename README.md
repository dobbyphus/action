# dobbyphus

A reusable GitHub Action that runs AI agents using
[opencode](https://github.com/sst/opencode) +
[oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode).

## Quick Start

```yaml
name: AI Agent

on:
  workflow_dispatch:
    inputs:
      prompt:
        description: Custom prompt to run
        required: false
      issue_number:
        description: Issue/PR number to comment on
        required: false

  issue_comment:
    types: [created]

  pull_request:
    types: [review_requested]

  pull_request_review:
    types: [submitted]

  pull_request_review_comment:
    types: [created]

jobs:
  agent:
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event_name == 'issue_comment' &&
       contains(github.event.comment.body, '@ai-agent') &&
       github.event.comment.user.login != 'github-actions[bot]' &&
       contains(fromJSON('["OWNER", "MEMBER", "COLLABORATOR"]'), github.event.comment.author_association)) ||
      (github.event_name == 'pull_request' &&
       github.event.requested_reviewer.login == 'github-actions[bot]') ||
      (github.event_name == 'pull_request_review' &&
       github.event.review.user.login != 'github-actions[bot]' &&
       contains(github.event.review.body, '@ai-agent')) ||
      (github.event_name == 'pull_request_review_comment' &&
       contains(github.event.comment.body, '@ai-agent') &&
       github.event.comment.user.login != 'github-actions[bot]' &&
       contains(fromJSON('["OWNER", "MEMBER", "COLLABORATOR"]'), github.event.comment.author_association))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref || github.ref }}
          fetch-depth: 0

      - uses: dobbyphus/action@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          bot_name: ai-agent
```

See [`examples/agent.yaml`](./examples/agent.yaml) for a complete workflow with mode detection and GitHub App token comments.

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `bot_name` | `ai-agent` | Bot name for labels and mentions |
| `mention_users` | `false` | Whether to @mention users in comments |
| `include_usernames` | `true` | Whether to include usernames at all (set `false` to remove entirely) |
| `anthropic_api_key` | - | Anthropic API key |
| `openai_api_key` | - | OpenAI API key |
| `gemini_api_key` | - | Google Gemini API key |
| `anthropic_base_url` | - | Custom Anthropic API base URL (for proxies) |
| `openai_base_url` | - | Custom OpenAI API base URL (for proxies) |
| `model_preset` | `balanced` | Preset: `balanced`, `fast`, `powerful` |
| `primary_model` | - | Override primary agent model |
| `oracle_model` | - | Override oracle agent model |
| `fast_model` | - | Override fast agents model |
| `mode` | `agent` | Prompt mode (maps to `{prompt_path}/{mode}.md`) |
| `prompt` | - | Direct prompt text (alternative to mode) |
| `prompt_path` | `.github/prompts` | Path to prompts directory |
| `prompt_vars` | - | JSON object for template substitution |
| `github_token` | `github.token` | GitHub token for API access |
| `opencode_version` | `latest` | OpenCode version to install |
| `oh_my_opencode_version` | `latest` | oh-my-opencode version to install |
| `config_json` | - | Full opencode.json content (advanced) |
| `omo_config_json` | - | Full oh-my-opencode.json content (advanced) |
| `auth_json` | - | Full auth.json content (advanced) |
| `agent_keywords` | `ultrawork` | Keywords to prepend for agent mode (triggers oh-my-opencode modes) |
| `review_keywords` | `analyze` | Keywords to prepend for review mode (triggers oh-my-opencode modes) |

## How It Works

The action handles everything in a single step:

1. **Setup**: Collects context from the trigger event, configures git, adds 👀 reaction
2. **Run**: Executes the AI agent with the configured prompt
3. **Teardown**: Replays commits as signed, creates PRs, updates reaction to 👍 or 😕

### Modes

The action supports two modes via the `mode` input:

| Mode | Use Case | Prompt |
|------|----------|--------|
| `agent` | Issue comments, PR comments, workflow dispatch | Work on requests, make changes |
| `review` | PR opened, review requested | Review code, provide feedback |

### Trigger Conditions

Use job-level `if` to control when the agent runs. The example covers:

- `workflow_dispatch`: Always run on manual trigger
- `issue_comment`: @mention by authorized user
- `pull_request`: Non-draft PR opened or ready for review
- `pull_request_review`: @mention in review body
- `pull_request_review_comment`: @mention in inline diff comment

### Branch & PR Workflow

The agent must create a branch for any changes. Direct commits to the default branch are blocked.

1. Agent creates a branch: `git checkout -b fix/issue-42`
2. Agent makes commits with meaningful messages
3. Action automatically:
   - Replays commits as signed via GitHub API
   - Creates the branch on remote if new
   - Opens a pull request to the default branch

### Signed Commits

All commits are signed and verified by GitHub. The agent commits normally using `git commit`, and the action replays each commit through the GitHub API, which signs them automatically.

### Workflow by Trigger

| Trigger | Mode | Agent Should | Action Does |
|---------|------|--------------|-------------|
| Issue comment | `agent` | Create branch, commit | Push branch, create PR |
| PR comment | `agent` | Commit to PR branch | Push to PR branch |
| PR inline comment | `review` | Review code, respond | Commit to PR branch |
| Workflow dispatch | `agent` | Create branch, commit | Push branch, create PR |
| PR opened | `review` | Review code | Post review comment |
| Review request | `review` | Review code | Post review comment |

## Configuration

### Repository Variables

Set these in Settings → Secrets and variables → Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_NAME` | `ai-agent` | Bot mention trigger and label prefix |
| `BOT_LOGIN` | `github-actions[bot]` | Bot login to prevent self-triggering |

### Model Presets

| Preset | Primary | Oracle | Fast |
|--------|---------|--------|------|
| `balanced` | claude-sonnet-4-5 | claude-sonnet-4-5 | claude-haiku-4-5 |
| `fast` | claude-haiku-4-5 | claude-haiku-4-5 | claude-haiku-4-5 |
| `powerful` | claude-opus-4-5 | gpt-5.2 | claude-sonnet-4-5 |

Override individual models with `primary_model`, `oracle_model`, `fast_model` inputs.

## Authentication

The action accepts a `github_token` input. Choose the right token for your use case:

### Default Token

The simplest option. Uses the automatic `GITHUB_TOKEN`:

```yaml
- uses: dobbyphus/action@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Limitations**: Cannot trigger other workflows, limited API rate, commits attributed to `github-actions[bot]`.

### GitHub App Token

For production use. Provides higher API limits, can trigger workflows, and commits are attributed to your app:

```yaml
- uses: actions/create-github-app-token@v1
  id: app-token
  with:
    app-id: ${{ vars.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}

- uses: actions/checkout@v4
  with:
    ref: ${{ github.head_ref || github.ref }}
    fetch-depth: 0
    token: ${{ steps.app-token.outputs.token }}

- uses: dobbyphus/action@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ steps.app-token.outputs.token }}
```

**Setup**: Create a GitHub App with `contents: write`, `issues: write`, `pull-requests: write` permissions. Store the App ID in a variable and the private key as a secret.

See the commented section in [`examples/agent.yaml`](./examples/agent.yaml) for the complete pattern.

### Personal Access Token

For individual use or cross-repository access:

```yaml
- uses: dobbyphus/action@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ secrets.PAT_TOKEN }}
```

## Prompt Templating

Templates use `{{ variable }}` syntax with multi-pass resolution:

```markdown
# {{ title }}

{{ base_github_env }}

Hello @{{ author }}, working on {{ task }}...
```

### Base Snippets

Place `.md` files in `prompts/base/` to create reusable snippets:

```
.github/prompts/
├── base/
│   └── my_rules.md   → {{ base_my_rules }}
├── agent.md
└── review.md
```

For project conventions, use `AGENTS.md` in the repository root instead. The agent checks for `AGENTS.md`, `CLAUDE.md`, and `COPILOT.md` automatically.

### Override Priority

Variables are merged with later sources overriding earlier ones:

1. Action's `prompts/base/*.md` (lowest priority)
2. Consumer's `prompt_path/base/*.md`
3. User-provided `prompt_vars` (highest priority)

## Development

```bash
python -m pytest tests/ -v
```

## License

MIT
