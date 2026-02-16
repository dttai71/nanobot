"""
Unit tests for agent/tools/registry.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.base import Tool


class MockTool(Tool):
    """Concrete Tool for testing."""

    def __init__(self, tool_name="mock_tool"):
        self._name = tool_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "A mock tool"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "arg1": {"type": "string", "description": "First arg"}
            },
            "required": ["arg1"],
        }

    async def execute(self, arg1: str = "", **kwargs) -> str:
        return f"executed: {arg1}"


class TestToolRegistryInit:
    def test_empty(self):
        reg = ToolRegistry()
        assert len(reg) == 0
        assert reg.tool_names == []


class TestToolRegistryRegister:
    def test_register(self):
        reg = ToolRegistry()
        tool = MockTool()
        reg.register(tool)
        assert len(reg) == 1
        assert "mock_tool" in reg

    def test_register_multiple(self):
        reg = ToolRegistry()
        reg.register(MockTool("tool_a"))
        reg.register(MockTool("tool_b"))
        assert len(reg) == 2

    def test_register_override(self):
        reg = ToolRegistry()
        reg.register(MockTool("same"))
        reg.register(MockTool("same"))
        assert len(reg) == 1

    def test_unregister(self):
        reg = ToolRegistry()
        reg.register(MockTool("to_remove"))
        reg.unregister("to_remove")
        assert len(reg) == 0

    def test_unregister_nonexistent(self):
        reg = ToolRegistry()
        reg.unregister("nope")  # Should not raise


class TestToolRegistryGet:
    def test_get_existing(self):
        reg = ToolRegistry()
        tool = MockTool()
        reg.register(tool)
        assert reg.get("mock_tool") is tool

    def test_get_nonexistent(self):
        reg = ToolRegistry()
        assert reg.get("nope") is None

    def test_has(self):
        reg = ToolRegistry()
        reg.register(MockTool())
        assert reg.has("mock_tool") is True
        assert reg.has("nope") is False

    def test_contains(self):
        reg = ToolRegistry()
        reg.register(MockTool())
        assert "mock_tool" in reg
        assert "nope" not in reg


class TestToolRegistryDefinitions:
    def test_get_definitions(self):
        reg = ToolRegistry()
        reg.register(MockTool("tool_a"))
        reg.register(MockTool("tool_b"))
        defs = reg.get_definitions()
        assert len(defs) == 2
        names = [d["function"]["name"] for d in defs]
        assert "tool_a" in names
        assert "tool_b" in names


class TestToolRegistryExecute:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        reg = ToolRegistry()
        reg.register(MockTool())
        result = await reg.execute("mock_tool", {"arg1": "hello"})
        assert result == "executed: hello"

    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        reg = ToolRegistry()
        result = await reg.execute("nope", {})
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_error(self):
        reg = ToolRegistry()
        tool = MockTool()
        tool.execute = AsyncMock(side_effect=RuntimeError("boom"))
        reg.register(tool)
        result = await reg.execute("mock_tool", {"arg1": "x"})
        assert "error" in result.lower()


class TestToolRegistryProperties:
    def test_tool_names(self):
        reg = ToolRegistry()
        reg.register(MockTool("a"))
        reg.register(MockTool("b"))
        names = reg.tool_names
        assert sorted(names) == ["a", "b"]

    def test_len(self):
        reg = ToolRegistry()
        assert len(reg) == 0
        reg.register(MockTool())
        assert len(reg) == 1
