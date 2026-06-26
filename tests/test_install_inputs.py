#!/usr/bin/env python3

import os
from pathlib import Path
import subprocess
import tempfile


ACTION_YAML = Path(__file__).parent.parent / "action.yaml"
INSTALL_SCRIPT = Path(__file__).parent.parent / "scripts" / "install.sh"
CONFIGURE_SCRIPT = Path(__file__).parent.parent / "scripts" / "configure.sh"


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

    def test_configure_receives_provider_inputs(self):
        action_text = ACTION_YAML.read_text()

        assert "PROVIDER_ANTHROPIC: ${{ inputs.provider_anthropic }}" in action_text
        assert "PROVIDER_OPENAI: ${{ inputs.provider_openai }}" in action_text
        assert "PROVIDER_GOOGLE: ${{ inputs.provider_google }}" in action_text
        assert "PROVIDER_COPILOT: ${{ inputs.provider_copilot }}" in action_text
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

    def test_action_exposes_opencode_print_logs_input(self):
        action_text = ACTION_YAML.read_text()

        assert "opencode_print_logs:" in action_text
        assert "Include raw opencode runtime logs" in action_text
        assert "OPENCODE_PRINT_LOGS: ${{ inputs.opencode_print_logs }}" in action_text

    def test_action_exposes_bot_login_input(self):
        action_text = ACTION_YAML.read_text()

        assert "bot_login:" in action_text
        assert "Optional GitHub login expected to author review output" in action_text

    def test_review_output_verification_uses_pagination(self):
        action_text = ACTION_YAML.read_text()

        assert "Resolve actor login" in action_text
        assert "Add eyes reaction" in action_text
        assert "Capture review baseline" in action_text
        assert "Verify review output" in action_text
        assert "gh api --paginate" in action_text
        assert "steps.mode.outputs.value == 'review'" in action_text
        assert "REQUESTED_REVIEWER_LOGIN" in action_text
        assert "REACTION_USER_LOGIN" in action_text

    def test_review_output_verification_is_folded_into_final_status(self):
        action_text = ACTION_YAML.read_text()

        assert "continue-on-error: true" in action_text
        assert "Determine final exit code" in action_text
        assert "steps.review_output.outputs.exit_code" in action_text
        assert "steps.final_status.outputs.exit_code" in action_text

    def test_install_passes_extended_provider_flags(self):
        install_text = INSTALL_SCRIPT.read_text()

        assert '--opencode-zen="${PROVIDER_OPENCODE_ZEN:-no}"' in install_text
        assert '--zai-coding-plan="${PROVIDER_ZAI_CODING_PLAN:-no}"' in install_text
        assert '--kimi-for-coding="${PROVIDER_KIMI_FOR_CODING:-no}"' in install_text
        assert '--opencode-go="${PROVIDER_OPENCODE_GO:-no}"' in install_text

    def test_configure_dumps_only_top_level_opencode_config_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            home = tmppath / "home"
            config_dir = home / ".config" / "opencode"
            nested = config_dir / "node_modules"
            nested.mkdir(parents=True)
            (nested / "ignored.json").write_text('{"nested": true}')

            result = subprocess.run(
                ["bash", str(CONFIGURE_SCRIPT)],
                check=True,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "ACTION_PATH": str(ACTION_YAML.parent),
                    "HOME": str(home),
                    "AUTH_JSON": '{"github-copilot": {"type": "oauth", "refresh": "x", "access": "x", "expires": 0}}',
                    "PROVIDER_ANTHROPIC": "no",
                    "PROVIDER_COPILOT": "yes",
                },
            )

            assert "==> " in result.stdout
            assert "opencode.json" in result.stdout
            assert "oh-my-opencode.json" in result.stdout
            assert "ignored.json" not in result.stdout
            assert '{"nested": true}' not in result.stdout
