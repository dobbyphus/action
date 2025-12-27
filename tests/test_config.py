#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from config import generate_auth, generate_omo_config, PRESETS, FAST_AGENTS


class TestGenerateAuth:
    def test_empty_when_no_keys(self):
        assert generate_auth(None, None, None) == {}

    def test_anthropic_only(self):
        result = generate_auth("sk-ant-123", None, None)
        assert result == {"anthropic": {"apiKey": "sk-ant-123"}}

    def test_openai_only(self):
        result = generate_auth(None, "sk-openai-123", None)
        assert result == {"openai": {"apiKey": "sk-openai-123"}}

    def test_gemini_only(self):
        result = generate_auth(None, None, "gemini-key")
        assert result == {"google": {"apiKey": "gemini-key"}}

    def test_all_providers(self):
        result = generate_auth("ant", "oai", "gem")
        assert result == {
            "anthropic": {"apiKey": "ant"},
            "openai": {"apiKey": "oai"},
            "google": {"apiKey": "gem"},
        }


class TestGenerateOmoConfig:
    def test_balanced_preset(self):
        result = generate_omo_config("balanced", None, None, None)
        agents = result["agents"]
        assert agents["Sisyphus"]["model"] == PRESETS["balanced"]["primary"]
        assert agents["oracle"]["model"] == PRESETS["balanced"]["oracle"]
        for agent in FAST_AGENTS:
            assert agents[agent]["model"] == PRESETS["balanced"]["fast"]

    def test_fast_preset(self):
        result = generate_omo_config("fast", None, None, None)
        agents = result["agents"]
        assert agents["Sisyphus"]["model"] == PRESETS["fast"]["primary"]

    def test_powerful_preset(self):
        result = generate_omo_config("powerful", None, None, None)
        agents = result["agents"]
        assert agents["Sisyphus"]["model"] == PRESETS["powerful"]["primary"]
        assert agents["oracle"]["model"] == PRESETS["powerful"]["oracle"]

    def test_unknown_preset_defaults_to_balanced(self):
        result = generate_omo_config("nonexistent", None, None, None)
        agents = result["agents"]
        assert agents["Sisyphus"]["model"] == PRESETS["balanced"]["primary"]

    def test_primary_override(self):
        result = generate_omo_config("balanced", "custom/model", None, None)
        assert result["agents"]["Sisyphus"]["model"] == "custom/model"

    def test_oracle_override(self):
        result = generate_omo_config("balanced", None, "custom/oracle", None)
        assert result["agents"]["oracle"]["model"] == "custom/oracle"

    def test_fast_override(self):
        result = generate_omo_config("balanced", None, None, "custom/fast")
        for agent in FAST_AGENTS:
            assert result["agents"][agent]["model"] == "custom/fast"

    def test_all_overrides(self):
        result = generate_omo_config("balanced", "p", "o", "f")
        agents = result["agents"]
        assert agents["Sisyphus"]["model"] == "p"
        assert agents["oracle"]["model"] == "o"
        for agent in FAST_AGENTS:
            assert agents[agent]["model"] == "f"
