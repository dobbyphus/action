#!/usr/bin/env python3

import os
from pathlib import Path
import subprocess
import tempfile


ACTION_YAML = Path(__file__).parent.parent / "action.yaml"
INSTALL_SCRIPT = Path(__file__).parent.parent / "scripts" / "install.sh"
CONFIGURE_SCRIPT = Path(__file__).parent.parent / "scripts" / "configure.sh"
VERSION_SCRIPT = Path(__file__).parent.parent / "scripts" / "version.sh"


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
        assert "required for pull_request" in action_text

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
        assert (
            action_text.count("steps.context.outputs.context_type == 'pr_opened'") == 3
        )

    def test_install_receives_token_and_configure_receives_omo_version(self):
        action_text = ACTION_YAML.read_text()

        install_step = action_text.split("- name: Install", 1)[1].split(
            "- name: Configure", 1
        )[0]
        configure_step = action_text.split("- name: Configure", 1)[1].split(
            "# === RUN AGENT ===", 1
        )[0]

        assert "GH_TOKEN: ${{ inputs.github_token }}" in install_step
        assert "env -u GH_TOKEN" in INSTALL_SCRIPT.read_text()
        assert (
            "OH_MY_OPENCODE_VERSION: ${{ steps.version.outputs.oh_my_opencode }}"
            in configure_step
        )

    def test_latest_omo_version_comes_from_npm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            fake_bin = tmppath / "bin"
            fake_bin.mkdir()
            output = tmppath / "output"

            (fake_bin / "gh").write_text("#!/bin/bash\necho v1.18.4\n")
            (fake_bin / "curl").write_text(
                "#!/bin/bash\n"
                '[[ "$*" == *registry.npmjs.org/oh-my-opencode/latest* ]] '
                "|| exit 2\n"
                "printf '%s\\n' '{\"version\":\"4.19.1\"}'\n"
            )
            for command in ("gh", "curl"):
                (fake_bin / command).chmod(0o755)

            subprocess.run(
                ["bash", str(VERSION_SCRIPT)],
                check=True,
                env={
                    **os.environ,
                    "GITHUB_OUTPUT": str(output),
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

            assert output.read_text().splitlines() == [
                "opencode=v1.18.4",
                "oh_my_opencode=v4.19.1",
            ]

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

    def test_install_rejects_bad_release_digest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            fake_bin = tmppath / "bin"
            fake_bin.mkdir()

            (fake_bin / "uname").write_text(
                '#!/bin/bash\n[[ "$1" == "-s" ]] && echo Darwin || echo arm64\n'
            )
            (fake_bin / "gh").write_text(
                "#!/bin/bash\n"
                "printf '%s\\n' "
                '\'{"assets":[{"name":"opencode-darwin-arm64.zip",'
                '"browser_download_url":"https://example.invalid/opencode.zip",'
                '"digest":"sha256:0000000000000000000000000000000000000000000000000000000000000000"}]}\'\n'
            )
            (fake_bin / "curl").write_text(
                "#!/bin/bash\n"
                "while [[ $# -gt 0 ]]; do\n"
                '  if [[ "$1" == "-o" ]]; then printf bad > "$2"; exit 0; fi\n'
                "  shift\n"
                "done\n"
            )
            for command in ("uname", "gh", "curl"):
                (fake_bin / command).chmod(0o755)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT)],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "HOME": str(tmppath / "home"),
                    "OPENCODE_VERSION": "v1.18.4",
                    "OH_MY_OPENCODE_VERSION": "v4.19.0",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

            assert result.returncode != 0
            assert "Checksum verification failed" in result.stderr

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
