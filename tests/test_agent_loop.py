"""
Unit tests for AgentLoop (nanobot/agent/loop.py).

Stage: 05 - TEST
Sprint: Sprint 01 - TT-005

Tests focus on:
- Initialization and default tool registration
- _run_agent_loop with mocked LLM responses
- _process_message slash commands
- _process_system_message routing
- process_direct convenience method
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None):
        super().__init__(api_key="test-key")
        self.responses = responses or []
        self._call_count = 0

    async def chat(self, messages, tools=None, model=None, max_tokens=4096, temperature=0.7):
        if self._call_count < len(self.responses):
            resp = self.responses[self._call_count]
            self._call_count += 1
            return resp
        return LLMResponse(content="Default response")

    def get_default_model(self) -> str:
        return "mock-model"


@pytest.fixture
def workspace(tmp_path):
    """Create a minimal workspace."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "AGENTS.md").write_text("Test agent", encoding="utf-8")
    return tmp_path


@pytest.fixture
def bus():
    return MessageBus()


@pytest.fixture
def provider():
    return MockProvider(responses=[LLMResponse(content="Hello from mock!")])


@pytest.fixture
def agent(bus, provider, workspace):
    from nanobot.agent.loop import AgentLoop
    return AgentLoop(
        bus=bus,
        provider=provider,
        workspace=workspace,
        model="mock-model",
        max_iterations=5,
    )


class TestAgentLoopInit:
    def test_default_model_from_provider(self, bus, workspace):
        provider = MockProvider()
        from nanobot.agent.loop import AgentLoop
        agent = AgentLoop(bus=bus, provider=provider, workspace=workspace)
        assert agent.model == "mock-model"

    def test_custom_model_override(self, bus, provider, workspace):
        from nanobot.agent.loop import AgentLoop
        agent = AgentLoop(bus=bus, provider=provider, workspace=workspace, model="custom-model")
        assert agent.model == "custom-model"

    def test_default_tools_registered(self, agent):
        tool_names = list(agent.tools._tools.keys())
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "edit_file" in tool_names
        assert "list_dir" in tool_names
        assert "exec" in tool_names
        assert "web_search" in tool_names
        assert "web_fetch" in tool_names
        assert "message" in tool_names
        assert "spawn" in tool_names

    def test_cron_tool_not_registered_without_service(self, agent):
        tool_names = list(agent.tools._tools.keys())
        assert "cron" not in tool_names

    def test_max_iterations(self, agent):
        assert agent.max_iterations == 5

    def test_initial_state_not_running(self, agent):
        assert agent._running is False


class TestRunAgentLoop:
    async def test_simple_text_response(self, agent):
        initial_messages = [
            {"role": "system", "content": "You are a test agent"},
            {"role": "user", "content": "Hello"},
        ]
        content, tools_used = await agent._run_agent_loop(initial_messages)
        assert content == "Hello from mock!"
        assert tools_used == []

    async def test_tool_call_then_response(self, bus, workspace):
        """Test agent loop with one tool call followed by a text response."""
        tool_call = ToolCallRequest(
            id="tc1", name="list_dir", arguments={"path": str(workspace)}
        )
        provider = MockProvider(responses=[
            LLMResponse(content=None, tool_calls=[tool_call]),
            LLMResponse(content="I listed the directory."),
        ])
        from nanobot.agent.loop import AgentLoop
        agent = AgentLoop(bus=bus, provider=provider, workspace=workspace, max_iterations=5)

        initial_messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "list files"},
        ]
        content, tools_used = await agent._run_agent_loop(initial_messages)
        assert content == "I listed the directory."
        assert "list_dir" in tools_used

    async def test_max_iterations_limit(self, bus, workspace):
        """Agent loop should stop after max_iterations even with continuous tool calls."""
        tool_call = ToolCallRequest(
            id="tc1", name="list_dir", arguments={"path": str(workspace)}
        )
        # Provider always returns tool calls, never a text response
        provider = MockProvider(responses=[
            LLMResponse(content=None, tool_calls=[tool_call]) for _ in range(10)
        ])
        from nanobot.agent.loop import AgentLoop
        agent = AgentLoop(bus=bus, provider=provider, workspace=workspace, max_iterations=3)

        initial_messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "keep calling tools"},
        ]
        content, tools_used = await agent._run_agent_loop(initial_messages)
        # Should stop after 3 iterations without final content
        assert content is None
        assert len(tools_used) == 3


class TestProcessMessage:
    async def test_slash_new_command(self, agent, bus):
        msg = InboundMessage(
            channel="telegram", sender_id="u1", chat_id="c1", content="/new"
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert "New session started" in response.content
        assert response.channel == "telegram"
        assert response.chat_id == "c1"

    async def test_slash_help_command(self, agent, bus):
        msg = InboundMessage(
            channel="discord", sender_id="u1", chat_id="c1", content="/help"
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert "/new" in response.content
        assert "/help" in response.content

    async def test_slash_help_case_insensitive(self, agent, bus):
        msg = InboundMessage(
            channel="telegram", sender_id="u1", chat_id="c1", content="/HELP"
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert "/help" in response.content

    async def test_normal_message_calls_llm(self, agent, bus):
        msg = InboundMessage(
            channel="telegram", sender_id="u1", chat_id="c1", content="What is 2+2?"
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert response.content == "Hello from mock!"
        assert response.channel == "telegram"

    async def test_session_persistence(self, agent, bus):
        """After processing a message, session should contain the exchange."""
        import uuid
        chat_id = f"persist-{uuid.uuid4().hex[:8]}"
        msg = InboundMessage(
            channel="telegram", sender_id="u1", chat_id=chat_id, content="Hello"
        )
        await agent._process_message(msg)

        session = agent.sessions.get_or_create(f"telegram:{chat_id}")
        assert len(session.messages) == 2  # user + assistant
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"


class TestProcessSystemMessage:
    async def test_system_message_routing(self, agent, bus):
        msg = InboundMessage(
            channel="system",
            sender_id="subagent-123",
            chat_id="telegram:c1",  # route back to telegram:c1
            content="Task completed: found 5 files",
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert response.channel == "telegram"
        assert response.chat_id == "c1"

    async def test_system_message_fallback(self, agent, bus):
        msg = InboundMessage(
            channel="system",
            sender_id="subagent",
            chat_id="no-colon-id",
            content="result",
        )
        response = await agent._process_message(msg)
        assert response is not None
        assert response.channel == "cli"


class TestProcessDirect:
    async def test_process_direct_basic(self, agent):
        result = await agent.process_direct("Hello")
        assert result == "Hello from mock!"

    async def test_process_direct_custom_session(self, agent):
        import uuid
        key = f"custom:{uuid.uuid4().hex[:8]}"
        result = await agent.process_direct(
            "test", session_key=key, channel="custom", chat_id=key.split(":")[1]
        )
        assert result == "Hello from mock!"

        session = agent.sessions.get_or_create(key)
        assert len(session.messages) == 2


class TestStopAndCleanup:
    def test_stop(self, agent):
        agent._running = True
        agent.stop()
        assert agent._running is False

    async def test_close_mcp_no_stack(self, agent):
        """close_mcp should not raise when no MCP stack exists."""
        await agent.close_mcp()  # Should not raise
