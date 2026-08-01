import importlib.util
import tempfile
from pathlib import Path


def load_prompt_module():
    prompt_path = Path(__file__).parent.parent / "scripts" / "prompt.py"
    spec = importlib.util.spec_from_file_location("prompt", prompt_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load prompt module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


find_prompt_file = load_prompt_module().find_prompt_file


class TestFindPromptFile:
    def test_finds_consumer_file_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action" / "prompts"
            consumer_dir.mkdir()
            action_dir.mkdir(parents=True)

            (consumer_dir / "agent.md").write_text("consumer")
            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file("agent", consumer_dir, tmppath / "action")
            assert result == consumer_dir / "agent.md"

    def test_falls_back_to_action_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action" / "prompts"
            consumer_dir.mkdir()
            action_dir.mkdir(parents=True)

            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file("agent", consumer_dir, tmppath / "action")
            assert result == action_dir / "agent.md"

    def test_returns_none_when_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            consumer_dir = tmppath / "consumer"
            action_dir = tmppath / "action"
            consumer_dir.mkdir()
            action_dir.mkdir()

            result = find_prompt_file("missing", consumer_dir, action_dir)
            assert result is None

    def test_nonexistent_consumer_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            action_dir = tmppath / "action" / "prompts"
            action_dir.mkdir(parents=True)

            (action_dir / "agent.md").write_text("action")

            result = find_prompt_file(
                "agent",
                tmppath / "nonexistent",
                tmppath / "action",
            )
            assert result == action_dir / "agent.md"


class TestGitHubActionPromptGuidance:
    def test_github_env_warns_about_one_shot_background_tasks(self):
        github_env = (
            Path(__file__).parent.parent / "prompts" / "base" / "github_env.md"
        ).read_text()

        assert "one-shot, non-interactive `opencode run` mode" in github_env
        assert (
            "NEVER end a response while background tasks are still pending"
            in github_env
        )
        assert (
            "Only launch background tasks if you can collect their results"
            in github_env
        )

    def test_agent_prompt_mentions_github_actions_exception(self):
        agent_prompt = (
            Path(__file__).parent.parent / "prompts" / "agent.md"
        ).read_text()

        assert "Exception: in GitHub Actions one-shot runs" in agent_prompt
        assert "do not finish with pending background tasks" in agent_prompt
