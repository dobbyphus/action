#!/usr/bin/env python3

import json
import os
from pathlib import Path

PRESETS = {
    "balanced": {
        "primary": "anthropic/claude-sonnet-4-5",
        "oracle": "anthropic/claude-sonnet-4-5",
        "fast": "anthropic/claude-haiku-4-5",
    },
    "fast": {
        "primary": "anthropic/claude-haiku-4-5",
        "oracle": "anthropic/claude-haiku-4-5",
        "fast": "anthropic/claude-haiku-4-5",
    },
    "powerful": {
        "primary": "anthropic/claude-opus-4-5",
        "oracle": "openai/gpt-5.2",
        "fast": "anthropic/claude-sonnet-4-5",
    },
}

FAST_AGENTS = ["explore", "librarian", "document-writer", "multimodal-looker"]


def generate_auth(
    anthropic_key: str | None,
    openai_key: str | None,
    gemini_key: str | None,
) -> dict:
    auth = {}
    if anthropic_key:
        auth["anthropic"] = {"apiKey": anthropic_key}
    if openai_key:
        auth["openai"] = {"apiKey": openai_key}
    if gemini_key:
        auth["google"] = {"apiKey": gemini_key}
    return auth


def generate_omo_config(
    preset: str,
    primary_override: str | None,
    oracle_override: str | None,
    fast_override: str | None,
) -> dict:
    models = PRESETS.get(preset, PRESETS["balanced"]).copy()

    if primary_override:
        models["primary"] = primary_override
    if oracle_override:
        models["oracle"] = oracle_override
    if fast_override:
        models["fast"] = fast_override

    agents = {
        "Sisyphus": {"model": models["primary"]},
        "oracle": {"model": models["oracle"]},
    }

    for agent in FAST_AGENTS:
        agents[agent] = {"model": models["fast"]}

    return {"agents": agents}


def main():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    auth_json = os.environ.get("AUTH_JSON")
    omo_config_json = os.environ.get("OMO_CONFIG_JSON")
    preset = os.environ.get("MODEL_PRESET", "balanced")
    primary_override = os.environ.get("PRIMARY_MODEL")
    oracle_override = os.environ.get("ORACLE_MODEL")
    fast_override = os.environ.get("FAST_MODEL")

    auth_dir = Path.home() / ".local" / "share" / "opencode"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"

    if auth_json:
        auth_file.write_text(auth_json)
    else:
        auth = generate_auth(anthropic_key, openai_key, gemini_key)
        if auth:
            auth_file.write_text(json.dumps(auth, indent=2))

    auth_file.chmod(0o600)

    config_dir = Path.home() / ".config" / "opencode"
    config_dir.mkdir(parents=True, exist_ok=True)
    omo_file = config_dir / "oh-my-opencode.json"

    if omo_config_json:
        omo_file.write_text(omo_config_json)
    else:
        omo_config = generate_omo_config(
            preset, primary_override, oracle_override, fast_override
        )
        omo_file.write_text(json.dumps(omo_config, indent=2))

    print(f"Generated auth: {auth_file}")
    print(f"Generated config: {omo_file}")


if __name__ == "__main__":
    main()
