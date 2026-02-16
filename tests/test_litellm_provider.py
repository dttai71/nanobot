"""
Unit tests for LiteLLM Provider (litellm_provider.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-013
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

from nanobot.providers.litellm_provider import LiteLLMProvider
from nanobot.providers.base import LLMResponse, ToolCallRequest


def _make_litellm_response(
    content="Hello", finish_reason="stop",
    tool_calls=None, usage=None, reasoning_content=None,
):
    """Create a mock LiteLLM response object."""
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
        reasoning_content=reasoning_content,
    )
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    if usage:
        usage_obj = SimpleNamespace(**usage)
    else:
        usage_obj = None
    return SimpleNamespace(choices=[choice], usage=usage_obj)


class TestLiteLLMProviderInit:
    """Tests for LiteLLMProvider initialization."""

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_default_model(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        assert provider.get_default_model() == "anthropic/claude-opus-4-5"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_custom_model(self, mock_litellm):
        provider = LiteLLMProvider(default_model="gpt-4o", provider_name="openai")
        assert provider.get_default_model() == "gpt-4o"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_api_key_stored(self, mock_litellm):
        provider = LiteLLMProvider(api_key="test-key", provider_name="anthropic")
        assert provider.api_key == "test-key"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_api_base_stored(self, mock_litellm):
        provider = LiteLLMProvider(api_base="http://localhost:8000", provider_name="vllm")
        assert provider.api_base == "http://localhost:8000"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_extra_headers(self, mock_litellm):
        headers = {"X-Custom": "value"}
        provider = LiteLLMProvider(extra_headers=headers, provider_name="anthropic")
        assert provider.extra_headers == headers


class TestResolveModel:
    """Tests for _resolve_model() method."""

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_standard_provider_prefix(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        # deepseek-chat → deepseek/deepseek-chat
        resolved = provider._resolve_model("deepseek-chat")
        assert resolved == "deepseek/deepseek-chat"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_no_double_prefix(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        # already prefixed → no change
        resolved = provider._resolve_model("deepseek/deepseek-chat")
        assert resolved == "deepseek/deepseek-chat"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_no_prefix_for_anthropic(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        # Claude models have no litellm_prefix
        resolved = provider._resolve_model("claude-sonnet-4-5")
        assert resolved == "claude-sonnet-4-5"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_gateway_prefix(self, mock_litellm):
        provider = LiteLLMProvider(
            api_key="sk-or-test", provider_name="openrouter"
        )
        resolved = provider._resolve_model("claude-sonnet-4-5")
        assert resolved == "openrouter/claude-sonnet-4-5"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_gateway_strip_prefix(self, mock_litellm):
        provider = LiteLLMProvider(
            api_base="https://aihubmix.com/v1", provider_name="aihubmix"
        )
        # aihubmix strips "anthropic/" then adds "openai/"
        resolved = provider._resolve_model("anthropic/claude-3")
        assert resolved == "openai/claude-3"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_unknown_model_no_prefix(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        resolved = provider._resolve_model("unknown-model")
        assert resolved == "unknown-model"

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_gemini_prefix(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        resolved = provider._resolve_model("gemini-pro")
        assert resolved == "gemini/gemini-pro"


class TestParseResponse:
    """Tests for _parse_response()."""

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_simple_text_response(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        raw = _make_litellm_response(content="Hello world")
        resp = provider._parse_response(raw)
        assert isinstance(resp, LLMResponse)
        assert resp.content == "Hello world"
        assert resp.finish_reason == "stop"
        assert resp.has_tool_calls is False

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_usage_parsing(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        raw = _make_litellm_response(
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
        resp = provider._parse_response(raw)
        assert resp.usage["prompt_tokens"] == 10
        assert resp.usage["total_tokens"] == 30

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_tool_calls_parsing(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        tc = SimpleNamespace(
            id="tc-1",
            function=SimpleNamespace(
                name="search",
                arguments='{"query": "test"}'
            )
        )
        raw = _make_litellm_response(content=None, tool_calls=[tc])
        resp = provider._parse_response(raw)
        assert resp.has_tool_calls is True
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "search"
        assert resp.tool_calls[0].arguments == {"query": "test"}

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_tool_calls_dict_arguments(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        tc = SimpleNamespace(
            id="tc-1",
            function=SimpleNamespace(
                name="read",
                arguments={"path": "/tmp/file.txt"}  # already a dict
            )
        )
        raw = _make_litellm_response(content=None, tool_calls=[tc])
        resp = provider._parse_response(raw)
        assert resp.tool_calls[0].arguments == {"path": "/tmp/file.txt"}

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_reasoning_content(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        raw = _make_litellm_response(
            content="answer", reasoning_content="thinking..."
        )
        resp = provider._parse_response(raw)
        assert resp.reasoning_content == "thinking..."

    @patch("nanobot.providers.litellm_provider.litellm")
    def test_no_usage(self, mock_litellm):
        provider = LiteLLMProvider(provider_name="anthropic")
        raw = _make_litellm_response()
        resp = provider._parse_response(raw)
        assert resp.usage == {}


class TestChat:
    """Tests for the chat() method."""

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_successful_chat(self, mock_acompletion, mock_litellm):
        mock_acompletion.return_value = _make_litellm_response("Hi there!")
        provider = LiteLLMProvider(api_key="test-key", provider_name="anthropic")

        resp = await provider.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-sonnet-4-5",
        )
        assert resp.content == "Hi there!"
        mock_acompletion.assert_called_once()

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_chat_with_tools(self, mock_acompletion, mock_litellm):
        tc = SimpleNamespace(
            id="tc-1",
            function=SimpleNamespace(name="search", arguments='{"q": "test"}')
        )
        mock_acompletion.return_value = _make_litellm_response(
            content=None, tool_calls=[tc]
        )
        provider = LiteLLMProvider(api_key="test-key", provider_name="anthropic")

        tools = [{"type": "function", "function": {"name": "search"}}]
        resp = await provider.chat(
            messages=[{"role": "user", "content": "search for test"}],
            tools=tools,
            model="claude-sonnet-4-5",
        )
        assert resp.has_tool_calls is True
        # Verify tool_choice was set
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["tool_choice"] == "auto"

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_chat_error_handling(self, mock_acompletion, mock_litellm):
        mock_acompletion.side_effect = Exception("API rate limit")
        provider = LiteLLMProvider(api_key="test-key", provider_name="anthropic")

        resp = await provider.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-sonnet-4-5",
        )
        assert "Error calling LLM" in resp.content
        assert resp.finish_reason == "error"

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_max_tokens_clamped(self, mock_acompletion, mock_litellm):
        mock_acompletion.return_value = _make_litellm_response("ok")
        provider = LiteLLMProvider(api_key="test-key", provider_name="anthropic")

        await provider.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-sonnet-4-5",
            max_tokens=0,
        )
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["max_tokens"] >= 1

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_uses_default_model(self, mock_acompletion, mock_litellm):
        mock_acompletion.return_value = _make_litellm_response("ok")
        provider = LiteLLMProvider(
            api_key="test-key", default_model="gpt-4o",
            provider_name="openai"
        )

        await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        call_kwargs = mock_acompletion.call_args[1]
        assert "gpt-4o" in call_kwargs["model"]

    @patch("nanobot.providers.litellm_provider.litellm")
    @patch("nanobot.providers.litellm_provider.acompletion")
    @pytest.mark.asyncio
    async def test_extra_headers_passed(self, mock_acompletion, mock_litellm):
        mock_acompletion.return_value = _make_litellm_response("ok")
        headers = {"X-App-Code": "abc123"}
        provider = LiteLLMProvider(
            api_key="test-key", extra_headers=headers,
            provider_name="anthropic"
        )

        await provider.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="claude-sonnet-4-5",
        )
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["extra_headers"] == headers
