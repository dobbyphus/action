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
derive_provider_lists = config.derive_provider_lists
provider_enabled = config.provider_enabled
build_provider_overrides = config.build_provider_overrides
pin_omo_plugin = config.pin_omo_plugin


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


class TestProviderSelectionDerivation:
    def test_provider_enabled_treats_no_as_disabled(self):
        assert provider_enabled("yes") is True
        assert provider_enabled("max20") is True
        assert provider_enabled("no") is False
        assert provider_enabled(None) is False

    def test_derive_provider_lists_for_copilot_only(self):
        enabled, disabled = derive_provider_lists(
            {
                "provider_anthropic": "no",
                "provider_openai": "no",
                "provider_google": "no",
                "provider_copilot": "yes",
                "provider_opencode_zen": "no",
                "provider_zai_coding_plan": "no",
                "provider_kimi_for_coding": "no",
                "provider_opencode_go": "no",
            }
        )

        assert enabled == ["github-copilot"]
        assert disabled == [
            "anthropic",
            "openai",
            "google",
            "opencode",
            "zai-coding-plan",
            "kimi-for-coding",
            "opencode-go",
        ]

    def test_derive_provider_lists_maps_opencode_variants(self):
        enabled, disabled = derive_provider_lists(
            {
                "provider_anthropic": "no",
                "provider_openai": "no",
                "provider_google": "no",
                "provider_copilot": "no",
                "provider_opencode_zen": "yes",
                "provider_zai_coding_plan": "yes",
                "provider_kimi_for_coding": "yes",
                "provider_opencode_go": "yes",
            }
        )

        assert enabled == [
            "opencode",
            "zai-coding-plan",
            "kimi-for-coding",
            "opencode-go",
        ]
        assert disabled == ["anthropic", "openai", "google", "github-copilot"]

    def test_build_provider_overrides_derives_both_lists(self):
        result = build_provider_overrides(
            None,
            None,
            {
                "provider_anthropic": "no",
                "provider_openai": "no",
                "provider_google": "no",
                "provider_copilot": "yes",
                "provider_opencode_zen": "no",
                "provider_zai_coding_plan": "no",
                "provider_kimi_for_coding": "no",
                "provider_opencode_go": "no",
            },
        )

        assert result == {
            "enabled_providers": ["github-copilot"],
            "disabled_providers": [
                "anthropic",
                "openai",
                "google",
                "opencode",
                "zai-coding-plan",
                "kimi-for-coding",
                "opencode-go",
            ],
        }

    def test_build_provider_overrides_keeps_explicit_enabled_only(self):
        result = build_provider_overrides(
            '["github-copilot"]',
            None,
            {
                "provider_anthropic": "max20",
                "provider_openai": "no",
                "provider_google": "no",
                "provider_copilot": "yes",
                "provider_opencode_zen": "no",
                "provider_zai_coding_plan": "no",
                "provider_kimi_for_coding": "no",
                "provider_opencode_go": "no",
            },
        )

        assert result == {"enabled_providers": ["github-copilot"]}

    def test_build_provider_overrides_keeps_explicit_disabled_only(self):
        result = build_provider_overrides(
            None,
            '["anthropic"]',
            {
                "provider_anthropic": "no",
                "provider_openai": "no",
                "provider_google": "no",
                "provider_copilot": "yes",
                "provider_opencode_zen": "no",
                "provider_zai_coding_plan": "no",
                "provider_kimi_for_coding": "no",
                "provider_opencode_go": "no",
            },
        )

        assert result == {"disabled_providers": ["anthropic"]}


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


class TestPinOmoPlugin:
    def test_pins_installer_plugin_to_resolved_version(self):
        result = pin_omo_plugin(
            {"plugin": ["other-plugin", "oh-my-opencode@latest"]},
            "v4.19.0",
        )

        assert result["plugin"] == [
            "other-plugin",
            "oh-my-opencode@4.19.0",
        ]

    def test_leaves_config_without_omo_plugin_unchanged(self):
        original = {"plugin": ["other-plugin"]}

        assert pin_omo_plugin(original, "v4.19.0") == original
