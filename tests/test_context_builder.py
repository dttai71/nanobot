"""
Unit tests for ContextBuilder (nanobot/agent/context.py).

Stage: 05 - TEST
Sprint: Sprint 01 - TT-007
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from nanobot.agent.context import ContextBuilder


@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace with bootstrap files."""
    # Create memory directory
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()

    return tmp_path


@pytest.fixture
def workspace_with_files(workspace):
    """Workspace with bootstrap files populated."""
    (workspace / "AGENTS.md").write_text("You are a helpful assistant.", encoding="utf-8")
    (workspace / "SOUL.md").write_text("Be concise and accurate.", encoding="utf-8")
    (workspace / "USER.md").write_text("User prefers Vietnamese.", encoding="utf-8")
    return workspace


@pytest.fixture
def builder(workspace):
    return ContextBuilder(workspace)


@pytest.fixture
def builder_with_files(workspace_with_files):
    return ContextBuilder(workspace_with_files)


class TestContextBuilderIdentity:
    def test_system_prompt_contains_nanobot(self, builder):
        prompt = builder.build_system_prompt()
        assert "nanobot" in prompt

    def test_system_prompt_contains_workspace_path(self, builder):
        prompt = builder.build_system_prompt()
        assert str(builder.workspace) in prompt

    def test_system_prompt_contains_tools_description(self, builder):
        prompt = builder.build_system_prompt()
        assert "Read, write, and edit files" in prompt
        assert "Execute shell commands" in prompt

    def test_system_prompt_contains_memory_paths(self, builder):
        prompt = builder.build_system_prompt()
        assert "MEMORY.md" in prompt
        assert "HISTORY.md" in prompt


class TestBootstrapFiles:
    def test_no_bootstrap_files(self, builder):
        prompt = builder.build_system_prompt()
        # Should still have identity section
        assert "nanobot" in prompt

    def test_loads_agents_md(self, builder_with_files):
        prompt = builder_with_files.build_system_prompt()
        assert "You are a helpful assistant." in prompt

    def test_loads_soul_md(self, builder_with_files):
        prompt = builder_with_files.build_system_prompt()
        assert "Be concise and accurate." in prompt

    def test_loads_user_md(self, builder_with_files):
        prompt = builder_with_files.build_system_prompt()
        assert "User prefers Vietnamese." in prompt

    def test_ignores_missing_bootstrap_files(self, workspace):
        # Only create one file
        (workspace / "AGENTS.md").write_text("Agent instructions", encoding="utf-8")
        builder = ContextBuilder(workspace)
        prompt = builder.build_system_prompt()
        assert "Agent instructions" in prompt


class TestMemoryContext:
    def test_no_memory(self, builder):
        prompt = builder.build_system_prompt()
        # Memory section should not appear if no memory content
        assert "Long-term Memory" not in prompt

    def test_with_memory(self, workspace):
        memory_dir = workspace / "memory"
        memory_dir.mkdir(exist_ok=True)
        (memory_dir / "MEMORY.md").write_text("User is a developer in Hanoi", encoding="utf-8")

        builder = ContextBuilder(workspace)
        prompt = builder.build_system_prompt()
        assert "User is a developer in Hanoi" in prompt
        assert "Memory" in prompt


class TestBuildMessages:
    def test_basic_message_list(self, builder):
        messages = builder.build_messages(
            history=[], current_message="Hello", channel="telegram", chat_id="123"
        )
        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_includes_history(self, builder):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        messages = builder.build_messages(
            history=history, current_message="How are you?"
        )
        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["content"] == "Hi"
        assert messages[2]["content"] == "Hello!"
        assert messages[3]["content"] == "How are you?"

    def test_session_info_in_system_prompt(self, builder):
        messages = builder.build_messages(
            history=[], current_message="test",
            channel="telegram", chat_id="12345"
        )
        system_prompt = messages[0]["content"]
        assert "telegram" in system_prompt
        assert "12345" in system_prompt

    def test_no_session_info_without_channel(self, builder):
        messages = builder.build_messages(
            history=[], current_message="test"
        )
        system_prompt = messages[0]["content"]
        assert "Current Session" not in system_prompt

    def test_plain_text_without_media(self, builder):
        messages = builder.build_messages(
            history=[], current_message="no media"
        )
        assert messages[1]["content"] == "no media"


class TestToolResults:
    def test_add_tool_result(self, builder):
        messages = [{"role": "system", "content": "test"}]
        result = builder.add_tool_result(
            messages, tool_call_id="tc1", tool_name="read_file", result="file content"
        )
        assert len(result) == 2
        assert result[1]["role"] == "tool"
        assert result[1]["tool_call_id"] == "tc1"
        assert result[1]["name"] == "read_file"
        assert result[1]["content"] == "file content"


class TestAssistantMessage:
    def test_add_content_only(self, builder):
        messages = []
        result = builder.add_assistant_message(messages, content="Hello!")
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hello!"

    def test_add_with_tool_calls(self, builder):
        messages = []
        tool_calls = [{"id": "tc1", "type": "function", "function": {"name": "read_file"}}]
        result = builder.add_assistant_message(messages, content=None, tool_calls=tool_calls)
        assert result[0]["tool_calls"] == tool_calls
        assert result[0]["content"] == ""

    def test_add_with_reasoning_content(self, builder):
        messages = []
        result = builder.add_assistant_message(
            messages, content="answer", reasoning_content="thinking..."
        )
        assert result[0]["reasoning_content"] == "thinking..."

    def test_no_reasoning_key_when_none(self, builder):
        messages = []
        result = builder.add_assistant_message(messages, content="answer")
        assert "reasoning_content" not in result[0]
