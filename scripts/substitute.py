#!/usr/bin/env python3
import re
import sys
import json

TRANSFORM_LIMIT = 10
VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def substitute(template: str, variables: dict) -> str:
    def replace_var(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    for _ in range(TRANSFORM_LIMIT):
        result = VAR_PATTERN.sub(replace_var, template)

        if result == template:
            return template

        template = result

    unresolved = set(VAR_PATTERN.findall(template))

    if unresolved:
        print(
            f"Warning: unresolved variables after {TRANSFORM_LIMIT} passes: {unresolved}",
            file=sys.stderr,
        )

    return template


if __name__ == "__main__":
    template = sys.stdin.read()
    variables = json.loads(sys.argv[1])
    print(substitute(template, variables))
