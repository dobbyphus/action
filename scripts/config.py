#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path


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
        auth["anthropic"] = {"type": "api", "key": anthropic_key}
    if openai_key:
        auth["openai"] = {"type": "api", "key": openai_key}
    if gemini_key:
        auth["google"] = {"type": "api", "key": gemini_key}
    return auth


def build_auth(
    anthropic_key: str | None,
    openai_key: str | None,
    gemini_key: str | None,
    auth_json: str | None,
) -> dict:
    auth = generate_auth(anthropic_key, openai_key, gemini_key)
    if auth_json is None or not auth_json.strip():
        return auth
    auth_override = parse_json_object(auth_json, "AUTH_JSON")
    return merge_configs(auth, auth_override)


def generate_omo_config(
    commit_footer: str | None = None,
    include_co_authored_by: str | None = None,
    enable_git_master: str | None = None,
    enable_playwright: str | None = None,
    enable_frontend_ui_ux: str | None = None,
) -> dict:
    config: dict[str, object] = {}

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
    if auth_json is not None and not auth_json.strip():
        auth_json = None
    config_json = os.environ.get("CONFIG_JSON")
    enabled_providers = os.environ.get("ENABLED_PROVIDERS")
    disabled_providers = os.environ.get("DISABLED_PROVIDERS")
    omo_config_json = os.environ.get("OMO_CONFIG_JSON")
    primary_override = os.environ.get("PRIMARY_MODEL")
    if primary_override is not None and not primary_override.strip():
        primary_override = None
    commit_footer = os.environ.get("COMMIT_FOOTER")
    include_co_authored_by = os.environ.get("INCLUDE_CO_AUTHORED_BY")
    enable_git_master = os.environ.get("SKILL_ENABLE_GIT_MASTER")
    enable_playwright = os.environ.get("SKILL_ENABLE_PLAYWRIGHT")
    enable_frontend_ui_ux = os.environ.get("SKILL_ENABLE_FRONTEND_UI_UX")

    auth_dir = Path.home() / ".local" / "share" / "opencode"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"

    auth_json_provided = auth_json is not None
    try:
        auth = build_auth(anthropic_key, openai_key, gemini_key, auth_json)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if auth_json_provided or auth:
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

    try:
        base_config = read_json_object(config_file) if config_file.exists() else {}
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if provider_overrides:
        override_config = merge_configs(override_config, provider_overrides)

    merged_config = base_config
    if primary_override:
        merged_config = merge_configs(merged_config, {"model": primary_override})
    if override_config:
        merged_config = merge_configs(merged_config, override_config)
    config_file.write_text(json.dumps(merged_config, indent=2))

    omo_defaults = generate_omo_config(
        commit_footer,
        include_co_authored_by,
        enable_git_master,
        enable_playwright,
        enable_frontend_ui_ux,
    )

    try:
        omo_base = read_json_object(omo_file) if omo_file.exists() else {}
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    merged_omo = merge_configs(omo_base, omo_defaults)

    if omo_config_json:
        try:
            omo_override = parse_json_object(omo_config_json, "OMO_CONFIG_JSON")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        merged_omo = merge_configs(merged_omo, omo_override)

    omo_file.write_text(json.dumps(merged_omo, indent=2))

    print(f"Generated auth: {auth_file}")
    print(f"Generated opencode config: {config_file}")
    print(f"Generated config: {omo_file}")


if __name__ == "__main__":
    main()
