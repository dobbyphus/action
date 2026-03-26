#!/usr/bin/env python3

from pathlib import Path


ACTION_YAML = Path(__file__).parent.parent / "action.yaml"
INSTALL_SCRIPT = Path(__file__).parent.parent / "scripts" / "install.sh"


class TestProviderInstallInputs:
    def test_action_exposes_extended_provider_inputs(self):
        action_text = ACTION_YAML.read_text()

        assert "provider_opencode_zen:" in action_text
        assert "provider_zai_coding_plan:" in action_text
        assert "provider_kimi_for_coding:" in action_text
        assert "provider_opencode_go:" in action_text

        assert (
            "PROVIDER_OPENCODE_ZEN: ${{ inputs.provider_opencode_zen }}" in action_text
        )
        assert (
            "PROVIDER_ZAI_CODING_PLAN: ${{ inputs.provider_zai_coding_plan }}"
            in action_text
        )
        assert (
            "PROVIDER_KIMI_FOR_CODING: ${{ inputs.provider_kimi_for_coding }}"
            in action_text
        )
        assert "PROVIDER_OPENCODE_GO: ${{ inputs.provider_opencode_go }}" in action_text

    def test_install_passes_extended_provider_flags(self):
        install_text = INSTALL_SCRIPT.read_text()

        assert '--opencode-zen="${PROVIDER_OPENCODE_ZEN:-no}"' in install_text
        assert '--zai-coding-plan="${PROVIDER_ZAI_CODING_PLAN:-no}"' in install_text
        assert '--kimi-for-coding="${PROVIDER_KIMI_FOR_CODING:-no}"' in install_text
        assert '--opencode-go="${PROVIDER_OPENCODE_GO:-no}"' in install_text
