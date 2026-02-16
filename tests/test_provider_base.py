"""
Unit tests for Provider base classes (base.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-014
"""

import pytest

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class TestToolCallRequest:
    """Tests for ToolCallRequest dataclass."""

    def test_creation(self):
        tc = ToolCallRequest(id="tc-1", name="search", arguments={"query": "test"})
        assert tc.id == "tc-1"
        assert tc.name == "search"
        assert tc.arguments == {"query": "test"}

    def test_empty_arguments(self):
        tc = ToolCallRequest(id="tc-2", name="noop", arguments={})
        assert tc.arguments == {}

    def test_complex_arguments(self):
        args = {"path": "/tmp/file.txt", "content": "hello", "overwrite": True}
        tc = ToolCallRequest(id="tc-3", name="write_file", arguments=args)
        assert tc.arguments["overwrite"] is True


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_defaults(self):
        resp = LLMResponse(content="Hello")
        assert resp.content == "Hello"
        assert resp.tool_calls == []
        assert resp.finish_reason == "stop"
        assert resp.usage == {}
        assert resp.reasoning_content is None

    def test_has_tool_calls_false(self):
        resp = LLMResponse(content="No tools")
        assert resp.has_tool_calls is False

    def test_has_tool_calls_true(self):
        tc = ToolCallRequest(id="tc-1", name="search", arguments={"q": "test"})
        resp = LLMResponse(content=None, tool_calls=[tc])
        assert resp.has_tool_calls is True

    def test_none_content(self):
        resp = LLMResponse(content=None)
        assert resp.content is None

    def test_custom_finish_reason(self):
        resp = LLMResponse(content="err", finish_reason="error")
        assert resp.finish_reason == "error"

    def test_usage_dict(self):
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        resp = LLMResponse(content="ok", usage=usage)
        assert resp.usage["total_tokens"] == 30

    def test_reasoning_content(self):
        resp = LLMResponse(content="answer", reasoning_content="thinking step")
        assert resp.reasoning_content == "thinking step"

    def test_multiple_tool_calls(self):
        tcs = [
            ToolCallRequest(id="tc-1", name="search", arguments={"q": "a"}),
            ToolCallRequest(id="tc-2", name="read", arguments={"path": "/x"}),
        ]
        resp = LLMResponse(content=None, tool_calls=tcs)
        assert len(resp.tool_calls) == 2
        assert resp.tool_calls[0].name == "search"
        assert resp.tool_calls[1].name == "read"


class TestLLMProvider:
    """Tests for LLMProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_concrete_subclass(self):
        class MockProvider(LLMProvider):
            async def chat(self, messages, tools=None, model=None,
                           max_tokens=4096, temperature=0.7):
                return LLMResponse(content="mock")

            def get_default_model(self):
                return "mock-model"

        provider = MockProvider(api_key="test-key", api_base="http://localhost")
        assert provider.api_key == "test-key"
        assert provider.api_base == "http://localhost"
        assert provider.get_default_model() == "mock-model"

    def test_default_init_values(self):
        class MockProvider(LLMProvider):
            async def chat(self, messages, tools=None, model=None,
                           max_tokens=4096, temperature=0.7):
                return LLMResponse(content="mock")

            def get_default_model(self):
                return "mock-model"

        provider = MockProvider()
        assert provider.api_key is None
        assert provider.api_base is None

    @pytest.mark.asyncio
    async def test_chat_returns_response(self):
        class MockProvider(LLMProvider):
            async def chat(self, messages, tools=None, model=None,
                           max_tokens=4096, temperature=0.7):
                return LLMResponse(content=f"Echo: {messages[0]['content']}")

            def get_default_model(self):
                return "mock-model"

        provider = MockProvider()
        resp = await provider.chat([{"role": "user", "content": "hello"}])
        assert resp.content == "Echo: hello"
