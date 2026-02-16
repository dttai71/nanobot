"""
Unit tests for agent/tools/spawn.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from nanobot.agent.tools.spawn import SpawnTool


class TestSpawnToolInit:
    def test_properties(self):
        mgr = MagicMock()
        tool = SpawnTool(manager=mgr)
        assert tool.name == "spawn"
        assert tool.parameters["type"] == "object"
        assert "task" in tool.parameters["properties"]

    def test_set_context(self):
        mgr = MagicMock()
        tool = SpawnTool(manager=mgr)
        tool.set_context("telegram", "123")
        assert tool._origin_channel == "telegram"
        assert tool._origin_chat_id == "123"

    def test_default_context(self):
        mgr = MagicMock()
        tool = SpawnTool(manager=mgr)
        assert tool._origin_channel == "cli"
        assert tool._origin_chat_id == "direct"


class TestSpawnToolExecute:
    @pytest.mark.asyncio
    async def test_spawn_success(self):
        mgr = MagicMock()
        mgr.spawn = AsyncMock(return_value="Subagent started (id: abc123)")
        tool = SpawnTool(manager=mgr)
        tool.set_context("telegram", "123")
        result = await tool.execute(task="Search for Python docs", label="python-docs")
        assert "started" in result.lower() or "subagent" in result.lower()
        mgr.spawn.assert_called_once_with(
            task="Search for Python docs",
            label="python-docs",
            origin_channel="telegram",
            origin_chat_id="123",
        )

    @pytest.mark.asyncio
    async def test_spawn_default_context(self):
        mgr = MagicMock()
        mgr.spawn = AsyncMock(return_value="Started")
        tool = SpawnTool(manager=mgr)
        await tool.execute(task="do something")
        mgr.spawn.assert_called_once_with(
            task="do something",
            label=None,
            origin_channel="cli",
            origin_chat_id="direct",
        )
