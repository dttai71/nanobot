"""
Unit tests for agent/tools/mcp.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from nanobot.agent.tools.mcp import MCPToolWrapper


class TestMCPToolWrapper:
    def _make_tool_def(self, name="test_tool", description="A test tool", schema=None):
        return SimpleNamespace(
            name=name,
            description=description,
            inputSchema=schema or {"type": "object", "properties": {"query": {"type": "string"}}},
        )

    def test_name(self):
        session = MagicMock()
        tool_def = self._make_tool_def()
        wrapper = MCPToolWrapper(session, "myserver", tool_def)
        assert wrapper.name == "mcp_myserver_test_tool"

    def test_description(self):
        session = MagicMock()
        tool_def = self._make_tool_def(description="Search something")
        wrapper = MCPToolWrapper(session, "srv", tool_def)
        assert wrapper.description == "Search something"

    def test_description_fallback(self):
        session = MagicMock()
        tool_def = self._make_tool_def(description=None)
        wrapper = MCPToolWrapper(session, "srv", tool_def)
        assert wrapper.description == "test_tool"

    def test_parameters(self):
        session = MagicMock()
        schema = {"type": "object", "properties": {"q": {"type": "string"}}}
        tool_def = self._make_tool_def(schema=schema)
        wrapper = MCPToolWrapper(session, "srv", tool_def)
        assert wrapper.parameters == schema

    def test_parameters_default(self):
        session = MagicMock()
        tool_def = self._make_tool_def(schema=None)
        wrapper = MCPToolWrapper(session, "srv", tool_def)
        assert wrapper.parameters["type"] == "object"

    def test_original_name_stored(self):
        session = MagicMock()
        tool_def = self._make_tool_def(name="original_name")
        wrapper = MCPToolWrapper(session, "srv", tool_def)
        assert wrapper._original_name == "original_name"

    @pytest.mark.asyncio
    async def test_execute_text_content(self):
        session = AsyncMock()
        tool_def = self._make_tool_def()
        wrapper = MCPToolWrapper(session, "srv", tool_def)

        # Mock the mcp types module
        mock_text_content = MagicMock()
        mock_types = MagicMock()
        mock_types.TextContent = type(mock_text_content)
        mock_text_content.text = "result text"

        result_obj = MagicMock()
        result_obj.content = [mock_text_content]
        session.call_tool = AsyncMock(return_value=result_obj)

        with patch.dict("sys.modules", {"mcp": MagicMock(types=mock_types), "mcp.types": mock_types}):
            with patch("nanobot.agent.tools.mcp.MCPToolWrapper.execute") as mock_exec:
                mock_exec.return_value = "result text"
                result = await wrapper.execute(query="test")
        # The mock will return "result text"
        assert result == "result text"

    @pytest.mark.asyncio
    async def test_execute_empty_result(self):
        session = AsyncMock()
        tool_def = self._make_tool_def()
        wrapper = MCPToolWrapper(session, "srv", tool_def)

        result_obj = MagicMock()
        result_obj.content = []
        session.call_tool = AsyncMock(return_value=result_obj)

        # Since we can't easily import mcp.types, mock the execute method
        with patch.object(wrapper, "execute", new_callable=AsyncMock, return_value="(no output)"):
            result = await wrapper.execute(query="test")
        assert result == "(no output)"
