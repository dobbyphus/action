#!/usr/bin/env python3

import json
import os
import sys
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


def read_json_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} contains invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def parse_json_object(value: str, name: str) -> dict:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a JSON object")
    return data


def parse_provider_list(value: str, name: str) -> list[str]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is invalid JSON: {exc}") from exc
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"{name} must be a JSON array of strings")
    return data


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
    commit_footer: str | None = None,
    include_co_authored_by: str | None = None,
    enable_git_master: str | None = None,
    enable_playwright: str | None = None,
    enable_frontend_ui_ux: str | None = None,
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

    config: dict[str, object] = {"agents": agents}

    disabled_skills = []
    if enable_git_master != "true":
        disabled_skills.append("git-master")
    if enable_playwright != "true":
        disabled_skills.append("playwright")
    if enable_frontend_ui_ux != "true":
        disabled_skills.append("frontend-ui-ux")

    if disabled_skills:
        config["disabled_skills"] = disabled_skills

    git_master = {}
    if commit_footer is not None:
        git_master["commit_footer"] = commit_footer.lower() == "true"
    if include_co_authored_by is not None:
        git_master["include_co_authored_by"] = include_co_authored_by.lower() == "true"

    if git_master:
        config["git_master"] = git_master

    return config


def merge_configs(base: dict, override: dict) -> dict:
    merged = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged


def main():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    auth_json = os.environ.get("AUTH_JSON")
    config_json = os.environ.get("CONFIG_JSON")
    enabled_providers = os.environ.get("ENABLED_PROVIDERS")
    disabled_providers = os.environ.get("DISABLED_PROVIDERS")
    omo_config_json = os.environ.get("OMO_CONFIG_JSON")
    preset = os.environ.get("MODEL_PRESET", "balanced")
    primary_override = os.environ.get("PRIMARY_MODEL")
    oracle_override = os.environ.get("ORACLE_MODEL")
    fast_override = os.environ.get("FAST_MODEL")
    commit_footer = os.environ.get("COMMIT_FOOTER")
    include_co_authored_by = os.environ.get("INCLUDE_CO_AUTHORED_BY")
    enable_git_master = os.environ.get("SKILL_ENABLE_GIT_MASTER")
    enable_playwright = os.environ.get("SKILL_ENABLE_PLAYWRIGHT")
    enable_frontend_ui_ux = os.environ.get("SKILL_ENABLE_FRONTEND_UI_UX")

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
    config_file = config_dir / "opencode.json"
    omo_file = config_dir / "oh-my-opencode.json"

    provider_overrides = {}
    override_config = {}
    try:
        if config_json:
            override_config = parse_json_object(config_json, "CONFIG_JSON")
        if enabled_providers:
            provider_overrides["enabled_providers"] = parse_provider_list(
                enabled_providers,
                "ENABLED_PROVIDERS",
            )
        if disabled_providers:
            provider_overrides["disabled_providers"] = parse_provider_list(
                disabled_providers,
                "DISABLED_PROVIDERS",
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if config_json or provider_overrides:
        try:
            base_config = read_json_object(config_file) if config_file.exists() else {}
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        if provider_overrides:
            override_config = merge_configs(override_config, provider_overrides)

        merged_config = merge_configs(base_config, override_config)
        config_file.write_text(json.dumps(merged_config, indent=2))

    if omo_config_json:
        omo_file.write_text(omo_config_json)
    else:
        omo_config = generate_omo_config(
            preset,
            primary_override,
            oracle_override,
            fast_override,
            commit_footer,
            include_co_authored_by,
            enable_git_master,
            enable_playwright,
            enable_frontend_ui_ux,
        )
        omo_file.write_text(json.dumps(omo_config, indent=2))

    print(f"Generated auth: {auth_file}")
    print(f"Generated opencode config: {config_file}")
    print(f"Generated config: {omo_file}")


if __name__ == "__main__":
    main()
