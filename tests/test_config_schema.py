"""
Unit tests for config/schema.py - Config class methods.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path

from nanobot.config.schema import (
    Config,
    AgentsConfig,
    AgentDefaults,
    ChannelsConfig,
    ProvidersConfig,
    ProviderConfig,
    GatewayConfig,
    ToolsConfig,
    TelegramConfig,
    DiscordConfig,
    SlackConfig,
    ExecToolConfig,
)


class TestConfig:
    def test_defaults(self):
        config = Config()
        assert isinstance(config.agents, AgentsConfig)
        assert isinstance(config.channels, ChannelsConfig)
        assert isinstance(config.providers, ProvidersConfig)

    def test_workspace_path(self):
        config = Config()
        path = config.workspace_path
        assert isinstance(path, Path)
        assert "~" not in str(path)  # Should be expanded


class TestConfigGetProvider:
    def test_no_keys(self):
        config = Config()
        assert config.get_provider() is None

    def test_get_provider_by_model_keyword(self):
        config = Config()
        config.providers.anthropic.api_key = "test-key"
        p = config.get_provider("anthropic/claude-3-haiku")
        assert p is not None
        assert p.api_key == "test-key"

    def test_get_provider_fallback(self):
        config = Config()
        config.providers.openrouter.api_key = "or-key"
        p = config.get_provider("some/unknown-model")
        assert p is not None  # Falls back to first available

    def test_get_provider_name(self):
        config = Config()
        config.providers.deepseek.api_key = "ds-key"
        name = config.get_provider_name("deepseek/deepseek-chat")
        assert name == "deepseek"

    def test_get_provider_name_none(self):
        config = Config()
        assert config.get_provider_name() is None


class TestConfigGetApiKey:
    def test_no_keys(self):
        config = Config()
        assert config.get_api_key() is None

    def test_with_key(self):
        config = Config()
        config.providers.anthropic.api_key = "test-key"
        assert config.get_api_key("anthropic/claude-3") == "test-key"


class TestConfigGetApiBase:
    def test_no_base(self):
        config = Config()
        assert config.get_api_base() is None

    def test_explicit_base(self):
        config = Config()
        config.providers.openrouter.api_key = "key"
        config.providers.openrouter.api_base = "https://custom.api.com"
        base = config.get_api_base("openrouter/model")
        assert base == "https://custom.api.com"

    def test_default_gateway_base(self):
        config = Config()
        config.providers.openrouter.api_key = "key"
        base = config.get_api_base("openrouter/model")
        # OpenRouter is a gateway with a default API base
        assert base is not None


class TestAgentDefaults:
    def test_defaults(self):
        d = AgentDefaults()
        assert d.model == "anthropic/claude-opus-4-5"
        assert d.max_tokens == 8192
        assert d.temperature == 0.7
        assert d.max_tool_iterations == 20
        assert d.memory_window == 50


class TestChannelConfigs:
    def test_telegram_defaults(self):
        tg = TelegramConfig()
        assert tg.enabled is False
        assert tg.token == ""

    def test_discord_defaults(self):
        dc = DiscordConfig()
        assert dc.enabled is False

    def test_slack_defaults(self):
        sl = SlackConfig()
        assert sl.enabled is False


class TestProviderConfig:
    def test_defaults(self):
        p = ProviderConfig()
        assert p.api_key == ""
        assert p.api_base is None
        assert p.extra_headers is None


class TestExecToolConfig:
    def test_defaults(self):
        e = ExecToolConfig()
        assert e.timeout > 0


class TestToolsConfig:
    def test_defaults(self):
        t = ToolsConfig()
        assert t.restrict_to_workspace is False
