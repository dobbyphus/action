# Agent Guidelines for dobbyphus/action

This is a reusable GitHub Action that runs AI agents using opencode + oh-my-opencode.

## Project Structure

```
action.yaml          # Main composite action definition
scripts/             # Python and shell scripts called by the action
  config.py          # Generate auth and oh-my-opencode config
  prompt.py          # Find and load prompt templates
  substitute.py      # Template variable substitution
  vars.py            # Load and merge base snippets with user vars
  *.sh               # Shell scripts for install, configure, run
tests/               # pytest test files
prompts/             # Default prompt templates
  base/              # Reusable prompt snippets ({{ base_* }} vars)
  agent.md           # Default agent mode prompt
  review.md          # Default review mode prompt
examples/            # Example workflow files
```

## Commands

### Run all checks (what CI runs)

```bash
yamllint .
ruff check scripts/ tests/
ruff format scripts/ tests/ --check
shellcheck scripts/*.sh
pytest tests/ -v
```

### Run tests

```bash
pytest tests/ -v                           # All tests
pytest tests/test_config.py -v             # Single file
pytest tests/test_config.py::TestGenerateAuth -v  # Single class
pytest tests/test_config.py::TestGenerateAuth::test_anthropic_only -v  # Single test
```

### Fix formatting

```bash
ruff format scripts/ tests/
ruff check scripts/ tests/ --fix
```

## Python Style

### Version and Dependencies

- Python 3.11+ (uses modern type hint syntax like `str | None`)
- No external dependencies for scripts (stdlib only)
- pytest required only for running tests

### File Structure

```python
#!/usr/bin/env python3
"""Optional one-line module docstring."""

import stdlib_module
from stdlib_module import thing

from local_module import function


CONSTANTS_AT_TOP = "value"


def public_function(arg: str, optional: str | None = None) -> dict:
    # Implementation
    return {}


def main():
    # Entry point logic
    pass


if __name__ == "__main__":
    main()
```

### Type Hints

- Use on all function signatures
- Use modern syntax: `str | None` not `Optional[str]`
- Use `dict`, `list` not `Dict`, `List` (Python 3.9+)
- Return type required: `-> ReturnType` or `-> None`

### Naming

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `SCREAMING_SNAKE_CASE` for constants
- Prefix test classes with `Test`: `TestGenerateAuth`
- Prefix test methods with `test_`: `test_anthropic_only`

### Error Handling

- Use `sys.exit(1)` for CLI errors after printing to stderr
- Print errors to stderr: `print("Error: ...", file=sys.stderr)`
- Let exceptions propagate unless you have specific handling

### Imports in Tests

Tests use path manipulation to import from scripts/:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from module_name import function_to_test
```

## Shell Style

### Script Header

```bash
#!/bin/bash
set -euo pipefail
```

- `set -e`: Exit on error
- `set -u`: Error on undefined variables
- `set -o pipefail`: Propagate pipe failures

### Variables

```bash
# Default values
ACTION_PATH="${ACTION_PATH:-.}"
OPTIONAL_VAR="${OPTIONAL_VAR:-}"

# Quote all variable expansions
echo "$VARIABLE"
"$SCRIPT_PATH" "$ARG"
```

### Conditionals

```bash
if [[ -n "${VAR:-}" ]]; then
  # VAR is set and non-empty
fi

if [[ -f "$FILE" ]]; then
  # File exists
fi
```

## YAML Style

- Max line length: 120 characters
- Use yamllint disable comments for long lines in workflows:
  ```yaml
  # yamllint disable-line rule:line-length rule:comments
  uses: actions/checkout@abc123def456  # v4.0.0
  ```
- Pin actions to commit SHA with version comment
- Quote `"on"` key to avoid YAML boolean interpretation

## Test Style

### Class-based Tests

```python
class TestFunctionName:
    def test_specific_behavior(self):
        result = function_under_test(input)
        assert result == expected

    def test_edge_case(self):
        result = function_under_test(edge_input)
        assert result is None
```

### Use tempfile for filesystem tests

```python
def test_file_operation(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "file.txt").write_text("content")
        result = function_under_test(tmppath)
        assert result == expected
```

## Action Development

### Adding New Inputs

1. Add input definition to `action.yaml` under `inputs:`
2. Pass to scripts via environment variables in the relevant step
3. Update README.md inputs table

### Adding New Scripts

1. Create `scripts/new_script.py` with shebang and main guard
2. Create `tests/test_new_script.py` with test class
3. Run `ruff format` and `ruff check` before committing

### Prompt Templates

- Templates use `{{ variable }}` syntax
- Base snippets in `prompts/base/*.md` become `{{ base_filename }}`
- Multi-pass substitution resolves nested variables (up to 10 passes)
