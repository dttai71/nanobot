"""
Unit tests for agent/subagent.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from nanobot.agent.subagent import SubagentManager
from nanobot.bus.queue import MessageBus


def _make_manager(tmp_path):
    """Create a SubagentManager with mocked provider."""
    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    bus = MessageBus()
    return SubagentManager(
        provider=provider,
        workspace=tmp_path,
        bus=bus,
    )


class TestSubagentManagerInit:
    def test_defaults(self, tmp_path):
        mgr = _make_manager(tmp_path)
        assert mgr.workspace == tmp_path
        assert mgr.model == "test-model"
        assert mgr.temperature == 0.7
        assert mgr.max_tokens == 4096
        assert mgr._running_tasks == {}

    def test_custom(self, tmp_path):
        provider = MagicMock()
        provider.get_default_model.return_value = "default"
        bus = MessageBus()
        mgr = SubagentManager(
            provider=provider,
            workspace=tmp_path,
            bus=bus,
            model="custom-model",
            temperature=0.5,
            max_tokens=2048,
            brave_api_key="test-key",
            restrict_to_workspace=True,
        )
        assert mgr.model == "custom-model"
        assert mgr.temperature == 0.5
        assert mgr.max_tokens == 2048
        assert mgr.brave_api_key == "test-key"
        assert mgr.restrict_to_workspace is True


class TestSubagentBuildPrompt:
    def test_prompt_contains_workspace(self, tmp_path):
        mgr = _make_manager(tmp_path)
        prompt = mgr._build_subagent_prompt("Do a task")
        assert str(tmp_path) in prompt
        assert "subagent" in prompt.lower()
        assert "rules" in prompt.lower()

    def test_prompt_contains_time(self, tmp_path):
        mgr = _make_manager(tmp_path)
        prompt = mgr._build_subagent_prompt("task")
        assert "Current Time" in prompt


class TestSubagentRunningCount:
    def test_initially_zero(self, tmp_path):
        mgr = _make_manager(tmp_path)
        assert mgr.get_running_count() == 0


class TestSubagentAnnounce:
    @pytest.mark.asyncio
    async def test_announce_result(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.bus.publish_inbound = AsyncMock()
        await mgr._announce_result(
            task_id="abc",
            label="test-task",
            task="Do something",
            result="Done!",
            origin={"channel": "telegram", "chat_id": "123"},
            status="ok",
        )
        mgr.bus.publish_inbound.assert_called_once()
        msg = mgr.bus.publish_inbound.call_args[0][0]
        assert msg.channel == "system"
        assert msg.sender_id == "subagent"
        assert "telegram:123" in msg.chat_id
        assert "completed successfully" in msg.content

    @pytest.mark.asyncio
    async def test_announce_error(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.bus.publish_inbound = AsyncMock()
        await mgr._announce_result(
            task_id="abc",
            label="test-task",
            task="Do something",
            result="Error: boom",
            origin={"channel": "cli", "chat_id": "direct"},
            status="error",
        )
        msg = mgr.bus.publish_inbound.call_args[0][0]
        assert "failed" in msg.content
