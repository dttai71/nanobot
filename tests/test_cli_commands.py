"""
Unit tests for cli/commands.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from nanobot.cli.commands import (
    app,
    _is_exit_command,
    _create_workspace_templates,
    EXIT_COMMANDS,
)


runner = CliRunner()


class TestIsExitCommand:
    def test_exit(self):
        assert _is_exit_command("exit") is True

    def test_quit(self):
        assert _is_exit_command("quit") is True

    def test_slash_exit(self):
        assert _is_exit_command("/exit") is True

    def test_slash_quit(self):
        assert _is_exit_command("/quit") is True

    def test_colon_q(self):
        assert _is_exit_command(":q") is True

    def test_case_insensitive(self):
        assert _is_exit_command("EXIT") is True
        assert _is_exit_command("Quit") is True

    def test_not_exit(self):
        assert _is_exit_command("hello") is False
        assert _is_exit_command("") is False

    def test_exit_commands_set(self):
        assert isinstance(EXIT_COMMANDS, set)
        assert len(EXIT_COMMANDS) >= 4


class TestCreateWorkspaceTemplates:
    def test_creates_files(self, tmp_path):
        _create_workspace_templates(tmp_path)
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "SOUL.md").exists()
        assert (tmp_path / "USER.md").exists()
        assert (tmp_path / "memory" / "MEMORY.md").exists()
        assert (tmp_path / "memory" / "HISTORY.md").exists()
        assert (tmp_path / "skills").is_dir()

    def test_does_not_overwrite(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("custom")
        _create_workspace_templates(tmp_path)
        assert (tmp_path / "AGENTS.md").read_text() == "custom"


class TestOnboardCommand:
    def test_onboard_new(self, tmp_path):
        fake_config_path = tmp_path / "config.json"
        with patch("nanobot.config.loader.get_config_path", return_value=fake_config_path), \
             patch("nanobot.config.loader.save_config"), \
             patch("nanobot.utils.helpers.get_workspace_path", return_value=tmp_path / "workspace"):
            result = runner.invoke(app, ["onboard"])
            assert result.exit_code == 0


class TestVersionCallback:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "nanobot" in result.stdout.lower()


class TestCronCommands:
    def test_cron_list_empty(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "list"])
            assert result.exit_code == 0
            assert "no scheduled" in result.stdout.lower()

    def test_cron_add_every(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "add", "--name", "test", "--message", "hello", "--every", "60"])
            assert result.exit_code == 0
            assert "added" in result.stdout.lower() or "✓" in result.stdout

    def test_cron_add_cron_expr(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "add", "--name", "test", "--message", "hello", "--cron", "0 9 * * *"])
            assert result.exit_code == 0

    def test_cron_add_at(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "add", "--name", "test", "--message", "hello", "--at", "2099-12-31T23:59:00"])
            assert result.exit_code == 0

    def test_cron_add_no_schedule(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "add", "--name", "test", "--message", "hello"])
            assert result.exit_code == 1

    def test_cron_remove_not_found(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "remove", "fake-id"])
            assert result.exit_code == 0
            assert "not found" in result.stdout.lower()

    def test_cron_enable_not_found(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            result = runner.invoke(app, ["cron", "enable", "fake"])
            assert "not found" in result.stdout.lower()

    def test_cron_list_with_jobs(self, tmp_path):
        with patch("nanobot.config.loader.get_data_dir", return_value=tmp_path):
            runner.invoke(app, ["cron", "add", "--name", "my_job", "--message", "hi", "--every", "120"])
            result = runner.invoke(app, ["cron", "list"])
            assert result.exit_code == 0
            assert "my_job" in result.stdout


class TestChannelsStatusCommand:
    def test_channels_status(self):
        from nanobot.config.schema import Config
        with patch("nanobot.config.loader.load_config", return_value=Config()):
            result = runner.invoke(app, ["channels", "status"])
            assert result.exit_code == 0
            assert "telegram" in result.stdout.lower() or "channel" in result.stdout.lower()


class TestStatusCommand:
    def test_status(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")
        from nanobot.config.schema import Config
        with patch("nanobot.config.loader.load_config", return_value=Config()), \
             patch("nanobot.config.loader.get_config_path", return_value=config_path):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0


class TestPrintAgentResponse:
    def test_print_markdown(self):
        from nanobot.cli.commands import _print_agent_response
        _print_agent_response("Hello **world**", render_markdown=True)

    def test_print_plain(self):
        from nanobot.cli.commands import _print_agent_response
        _print_agent_response("Hello world", render_markdown=False)

    def test_print_empty(self):
        from nanobot.cli.commands import _print_agent_response
        _print_agent_response(None, render_markdown=True)


class TestMakeProvider:
    def test_make_provider_success(self):
        from nanobot.cli.commands import _make_provider
        from nanobot.config.schema import Config
        config = Config()
        # Set an API key so it doesn't exit
        config.providers.openrouter.api_key = "test-key"
        with patch("nanobot.providers.litellm_provider.litellm"):
            provider = _make_provider(config)
            assert provider is not None

    def test_make_provider_no_key(self):
        from nanobot.cli.commands import _make_provider
        from nanobot.config.schema import Config
        from click.exceptions import Exit
        config = Config()
        with pytest.raises(Exit):
            _make_provider(config)
