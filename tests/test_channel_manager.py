"""
Unit tests for ChannelManager (channels/manager.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-015
"""

import asyncio

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager


def _make_channel_config(enabled=False):
    """Create a minimal channel config stub."""
    return SimpleNamespace(enabled=enabled, allow_from=[], token="fake-token")


def _make_config(enabled_channels=None):
    """Create a minimal Config-like object with all channels disabled by default."""
    enabled_channels = enabled_channels or []
    channels = SimpleNamespace(
        telegram=_make_channel_config("telegram" in enabled_channels),
        whatsapp=_make_channel_config("whatsapp" in enabled_channels),
        discord=_make_channel_config("discord" in enabled_channels),
        feishu=_make_channel_config("feishu" in enabled_channels),
        mochat=_make_channel_config("mochat" in enabled_channels),
        dingtalk=_make_channel_config("dingtalk" in enabled_channels),
        email=_make_channel_config("email" in enabled_channels),
        slack=_make_channel_config("slack" in enabled_channels),
        qq=_make_channel_config("qq" in enabled_channels),
    )
    providers = SimpleNamespace(groq=SimpleNamespace(api_key=""))
    return SimpleNamespace(channels=channels, providers=providers)


class MockChannel(BaseChannel):
    """Mock channel for testing ChannelManager."""
    name = "mock"

    def __init__(self):
        self._running = False
        self.started = False
        self.stopped = False
        self.sent_messages = []

    async def start(self):
        self._running = True
        self.started = True

    async def stop(self):
        self._running = False
        self.stopped = True

    async def send(self, msg):
        self.sent_messages.append(msg)


class TestChannelManagerInit:
    """Tests for ChannelManager initialization."""

    def test_no_channels_enabled(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        assert mgr.channels == {}
        assert mgr.enabled_channels == []

    def test_stores_config_and_bus(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        assert mgr.config is config
        assert mgr.bus is bus

    def test_telegram_enabled(self):
        config = _make_config(["telegram"])
        bus = MessageBus()
        mock_tg = MagicMock()
        with patch("nanobot.channels.manager.TelegramChannel", mock_tg, create=True), \
             patch.dict("sys.modules", {"nanobot.channels.telegram": MagicMock(TelegramChannel=mock_tg)}):
            mgr = ChannelManager(config, bus)
            assert "telegram" in mgr.channels

    def test_discord_enabled(self):
        config = _make_config(["discord"])
        bus = MessageBus()
        mock_dc = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.discord": MagicMock(DiscordChannel=mock_dc)}):
            mgr = ChannelManager(config, bus)
            assert "discord" in mgr.channels

    def test_slack_enabled(self):
        config = _make_config(["slack"])
        bus = MessageBus()
        mock_sl = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.slack": MagicMock(SlackChannel=mock_sl)}):
            mgr = ChannelManager(config, bus)
            assert "slack" in mgr.channels

    def test_email_enabled(self):
        config = _make_config(["email"])
        bus = MessageBus()
        mock_em = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.email": MagicMock(EmailChannel=mock_em)}):
            mgr = ChannelManager(config, bus)
            assert "email" in mgr.channels

    def test_whatsapp_enabled(self):
        config = _make_config(["whatsapp"])
        bus = MessageBus()
        mock_wa = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.whatsapp": MagicMock(WhatsAppChannel=mock_wa)}):
            mgr = ChannelManager(config, bus)
            assert "whatsapp" in mgr.channels

    def test_feishu_enabled(self):
        config = _make_config(["feishu"])
        bus = MessageBus()
        mock_fs = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.feishu": MagicMock(FeishuChannel=mock_fs)}):
            mgr = ChannelManager(config, bus)
            assert "feishu" in mgr.channels

    def test_dingtalk_enabled(self):
        config = _make_config(["dingtalk"])
        bus = MessageBus()
        mock_dt = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.dingtalk": MagicMock(DingTalkChannel=mock_dt)}):
            mgr = ChannelManager(config, bus)
            assert "dingtalk" in mgr.channels

    def test_mochat_enabled(self):
        config = _make_config(["mochat"])
        bus = MessageBus()
        mock_mc = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.mochat": MagicMock(MochatChannel=mock_mc)}):
            mgr = ChannelManager(config, bus)
            assert "mochat" in mgr.channels

    def test_qq_enabled(self):
        config = _make_config(["qq"])
        bus = MessageBus()
        mock_qq = MagicMock()
        with patch.dict("sys.modules", {"nanobot.channels.qq": MagicMock(QQChannel=mock_qq)}):
            mgr = ChannelManager(config, bus)
            assert "qq" in mgr.channels


class TestGetChannel:
    """Tests for get_channel()."""

    def test_get_existing_channel(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mock_ch = MockChannel()
        mgr.channels["mock"] = mock_ch
        assert mgr.get_channel("mock") is mock_ch

    def test_get_nonexistent_channel(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        assert mgr.get_channel("nonexistent") is None


class TestGetStatus:
    """Tests for get_status()."""

    def test_empty_status(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        assert mgr.get_status() == {}

    def test_status_with_channels(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mock_ch = MockChannel()
        mgr.channels["mock"] = mock_ch
        status = mgr.get_status()
        assert "mock" in status
        assert status["mock"]["enabled"] is True
        assert status["mock"]["running"] is False


class TestEnabledChannels:
    """Tests for enabled_channels property."""

    def test_returns_channel_names(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mgr.channels["telegram"] = MockChannel()
        mgr.channels["discord"] = MockChannel()
        names = mgr.enabled_channels
        assert "telegram" in names
        assert "discord" in names


class TestStartAll:
    """Tests for start_all()."""

    @pytest.mark.asyncio
    async def test_no_channels_warns(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        # Should return without error when no channels
        await mgr.start_all()

    @pytest.mark.asyncio
    async def test_starts_channels_and_dispatcher(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mock_ch = MockChannel()
        mgr.channels["mock"] = mock_ch

        # start_all blocks, so run with timeout
        task = asyncio.create_task(mgr.start_all())
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert mock_ch.started is True
        assert mgr._dispatch_task is not None


class TestStopAll:
    """Tests for stop_all()."""

    @pytest.mark.asyncio
    async def test_stops_channels(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mock_ch = MockChannel()
        mock_ch._running = True
        mgr.channels["mock"] = mock_ch
        mgr._dispatch_task = asyncio.create_task(asyncio.sleep(100))

        await mgr.stop_all()
        assert mock_ch.stopped is True

    @pytest.mark.asyncio
    async def test_stop_with_no_dispatcher(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mgr._dispatch_task = None
        # Should not raise
        await mgr.stop_all()


class TestDispatchOutbound:
    """Tests for _dispatch_outbound() routing."""

    @pytest.mark.asyncio
    async def test_routes_to_correct_channel(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)
        mock_ch = MockChannel()
        mgr.channels["mock"] = mock_ch

        # Start dispatcher
        dispatch_task = asyncio.create_task(mgr._dispatch_outbound())
        await asyncio.sleep(0.05)

        # Publish outbound message
        msg = OutboundMessage(channel="mock", chat_id="c1", content="Hello")
        await bus.publish_outbound(msg)
        await asyncio.sleep(0.1)

        dispatch_task.cancel()
        try:
            await dispatch_task
        except asyncio.CancelledError:
            pass

        assert len(mock_ch.sent_messages) == 1
        assert mock_ch.sent_messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_unknown_channel_does_not_crash(self):
        config = _make_config()
        bus = MessageBus()
        mgr = ChannelManager(config, bus)

        dispatch_task = asyncio.create_task(mgr._dispatch_outbound())
        await asyncio.sleep(0.05)

        msg = OutboundMessage(channel="nonexistent", chat_id="c1", content="Hi")
        await bus.publish_outbound(msg)
        await asyncio.sleep(0.1)

        dispatch_task.cancel()
        try:
            await dispatch_task
        except asyncio.CancelledError:
            pass
        # Should not raise — just logs warning
