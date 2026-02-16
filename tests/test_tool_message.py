"""
Unit tests for agent/tools/message.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import AsyncMock

from nanobot.agent.tools.message import MessageTool
from nanobot.bus.events import OutboundMessage


class TestMessageToolInit:
    def test_defaults(self):
        tool = MessageTool()
        assert tool._send_callback is None
        assert tool._default_channel == ""
        assert tool._default_chat_id == ""

    def test_custom(self):
        cb = AsyncMock()
        tool = MessageTool(send_callback=cb, default_channel="telegram", default_chat_id="123")
        assert tool._send_callback is cb
        assert tool._default_channel == "telegram"
        assert tool._default_chat_id == "123"

    def test_properties(self):
        tool = MessageTool()
        assert tool.name == "message"
        assert tool.parameters["type"] == "object"
        assert "content" in tool.parameters["properties"]


class TestMessageToolSetContext:
    def test_set_context(self):
        tool = MessageTool()
        tool.set_context("discord", "456")
        assert tool._default_channel == "discord"
        assert tool._default_chat_id == "456"

    def test_set_send_callback(self):
        tool = MessageTool()
        cb = AsyncMock()
        tool.set_send_callback(cb)
        assert tool._send_callback is cb


class TestMessageToolExecute:
    @pytest.mark.asyncio
    async def test_send_success(self):
        cb = AsyncMock()
        tool = MessageTool(send_callback=cb, default_channel="telegram", default_chat_id="123")
        result = await tool.execute("Hello!")
        assert "sent" in result.lower()
        cb.assert_called_once()
        msg = cb.call_args[0][0]
        assert isinstance(msg, OutboundMessage)
        assert msg.content == "Hello!"
        assert msg.channel == "telegram"
        assert msg.chat_id == "123"

    @pytest.mark.asyncio
    async def test_send_custom_target(self):
        cb = AsyncMock()
        tool = MessageTool(send_callback=cb, default_channel="telegram", default_chat_id="123")
        result = await tool.execute("Hi!", channel="discord", chat_id="456")
        assert "discord" in result

    @pytest.mark.asyncio
    async def test_no_channel(self):
        cb = AsyncMock()
        tool = MessageTool(send_callback=cb)
        result = await tool.execute("hello")
        assert "error" in result.lower()
        assert "no target" in result.lower()

    @pytest.mark.asyncio
    async def test_no_callback(self):
        tool = MessageTool(default_channel="telegram", default_chat_id="123")
        result = await tool.execute("hello")
        assert "error" in result.lower()
        assert "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_send_error(self):
        cb = AsyncMock(side_effect=Exception("Network error"))
        tool = MessageTool(send_callback=cb, default_channel="telegram", default_chat_id="123")
        result = await tool.execute("hello")
        assert "error" in result.lower()
        assert "network error" in result.lower()
