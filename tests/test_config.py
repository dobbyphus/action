#!/usr/bin/env python3

import importlib.util
from pathlib import Path


def load_config_module():
    config_path = Path(__file__).parent.parent / "scripts" / "config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load config module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = load_config_module()
build_auth = config.build_auth
generate_auth = config.generate_auth
generate_omo_config = config.generate_omo_config
parse_provider_list = config.parse_provider_list


def assert_value_error(expected: str, func, *args):
    try:
        func(*args)
    except ValueError as exc:
        assert expected in str(exc)
        return
    raise AssertionError("Expected ValueError")


class TestGenerateAuth:
    def test_empty_when_no_keys(self):
        assert generate_auth(None, None, None) == {}

    def test_anthropic_only(self):
        result = generate_auth("sk-ant-123", None, None)
        assert result == {"anthropic": {"type": "api", "key": "sk-ant-123"}}

    def test_openai_only(self):
        result = generate_auth(None, "sk-openai-123", None)
        assert result == {"openai": {"type": "api", "key": "sk-openai-123"}}

    def test_gemini_only(self):
        result = generate_auth(None, None, "gemini-key")
        assert result == {"google": {"type": "api", "key": "gemini-key"}}

    def test_all_providers(self):
        result = generate_auth("ant", "oai", "gem")
        assert result == {
            "anthropic": {"type": "api", "key": "ant"},
            "openai": {"type": "api", "key": "oai"},
            "google": {"type": "api", "key": "gem"},
        }


class TestBuildAuth:
    def test_base_keys_only(self):
        result = build_auth("ant", None, None, None)
        assert result == {"anthropic": {"type": "api", "key": "ant"}}

    def test_auth_json_merges_and_overrides(self):
        auth_json = '{"openai": {"type": "api", "key": "override"}}'
        result = build_auth("ant", "oai", None, auth_json)
        assert result == {
            "anthropic": {"type": "api", "key": "ant"},
            "openai": {"type": "api", "key": "override"},
        }

    def test_auth_json_empty_object(self):
        result = build_auth("ant", None, None, "{}")
        assert result == {"anthropic": {"type": "api", "key": "ant"}}

    def test_auth_json_empty_string(self):
        result = build_auth("ant", None, None, "")
        assert result == {"anthropic": {"type": "api", "key": "ant"}}


class TestParseProviderList:
    def test_valid_list(self):
        result = parse_provider_list('["anthropic", "openai"]', "ENABLED_PROVIDERS")
        assert result == ["anthropic", "openai"]

    def test_invalid_json(self):
        assert_value_error(
            "ENABLED_PROVIDERS is invalid JSON",
            parse_provider_list,
            "not-json",
            "ENABLED_PROVIDERS",
        )

    def test_invalid_type(self):
        assert_value_error(
            "ENABLED_PROVIDERS must be a JSON array of strings",
            parse_provider_list,
            '{"anthropic": true}',
            "ENABLED_PROVIDERS",
        )

    def test_invalid_items(self):
        assert_value_error(
            "ENABLED_PROVIDERS must be a JSON array of strings",
            parse_provider_list,
            "[1]",
            "ENABLED_PROVIDERS",
        )


class TestGenerateOmoConfig:
    def test_git_master_config(self):
        result = generate_omo_config("true", "true")
        assert result["git_master"] == {
            "commit_footer": True,
            "include_co_authored_by": True,
        }

    def test_git_master_config_false(self):
        result = generate_omo_config("false", "false")
        assert result["git_master"] == {
            "commit_footer": False,
            "include_co_authored_by": False,
        }

    def test_git_master_config_mixed(self):
        result = generate_omo_config("true", "false")
        assert result["git_master"] == {
            "commit_footer": True,
            "include_co_authored_by": False,
        }

    def test_git_master_config_partial(self):
        result = generate_omo_config(None, "true")
        assert result["git_master"] == {
            "include_co_authored_by": True,
        }

    def test_git_master_config_none(self):
        result = generate_omo_config()
        assert "git_master" not in result

    def test_builtin_skills_default_disabled(self):
        result = generate_omo_config()
        assert result["disabled_skills"] == [
            "git-master",
            "playwright",
            "frontend-ui-ux",
        ]

    def test_builtin_skills_all_enabled(self):
        result = generate_omo_config(
            None,
            None,
            "true",
            "true",
            "true",
        )
        assert "disabled_skills" not in result

    def test_builtin_skills_partial_enabled(self):
        result = generate_omo_config(
            None,
            None,
            "true",
            None,
            "true",
        )
        assert result["disabled_skills"] == ["playwright"]
