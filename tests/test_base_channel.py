"""
Unit tests for BaseChannel (channels/base.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-016
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel


class ConcreteChannel(BaseChannel):
    """Concrete implementation of BaseChannel for testing."""
    name = "test_channel"

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    async def send(self, msg: OutboundMessage):
        self.last_sent = msg


@pytest.fixture
def bus():
    return MessageBus()


@pytest.fixture
def config_no_allow():
    return SimpleNamespace(allow_from=[])


@pytest.fixture
def config_with_allow():
    return SimpleNamespace(allow_from=["user1", "user2", "12345"])


class TestBaseChannelInit:
    """Tests for BaseChannel initialization."""

    def test_stores_config_and_bus(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        assert ch.config is config_no_allow
        assert ch.bus is bus

    def test_not_running_initially(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        assert ch.is_running is False

    def test_name_attribute(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        assert ch.name == "test_channel"


class TestIsAllowed:
    """Tests for is_allowed() access control."""

    def test_empty_allow_list_allows_everyone(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        assert ch.is_allowed("anyone") is True
        assert ch.is_allowed("12345") is True

    def test_allow_list_allows_listed_user(self, bus, config_with_allow):
        ch = ConcreteChannel(config_with_allow, bus)
        assert ch.is_allowed("user1") is True
        assert ch.is_allowed("12345") is True

    def test_allow_list_denies_unlisted_user(self, bus, config_with_allow):
        ch = ConcreteChannel(config_with_allow, bus)
        assert ch.is_allowed("unknown_user") is False

    def test_pipe_separated_sender(self, bus, config_with_allow):
        """sender_id with pipes should check each part."""
        ch = ConcreteChannel(config_with_allow, bus)
        assert ch.is_allowed("unknown|user1") is True
        assert ch.is_allowed("unknown|other") is False

    def test_numeric_sender_id_converted(self, bus, config_with_allow):
        ch = ConcreteChannel(config_with_allow, bus)
        assert ch.is_allowed(12345) is True


class TestHandleMessage:
    """Tests for _handle_message()."""

    @pytest.mark.asyncio
    async def test_publishes_inbound_message(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        bus.publish_inbound = AsyncMock()

        await ch._handle_message("sender1", "chat1", "Hello")
        bus.publish_inbound.assert_called_once()
        msg = bus.publish_inbound.call_args[0][0]
        assert isinstance(msg, InboundMessage)
        assert msg.channel == "test_channel"
        assert msg.sender_id == "sender1"
        assert msg.chat_id == "chat1"
        assert msg.content == "Hello"

    @pytest.mark.asyncio
    async def test_denied_sender_no_publish(self, bus, config_with_allow):
        ch = ConcreteChannel(config_with_allow, bus)
        bus.publish_inbound = AsyncMock()

        await ch._handle_message("blocked_user", "chat1", "Hello")
        bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_forwarded(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        bus.publish_inbound = AsyncMock()

        await ch._handle_message(
            "sender1", "chat1", "Photo", media=["http://img.jpg"]
        )
        msg = bus.publish_inbound.call_args[0][0]
        assert msg.media == ["http://img.jpg"]

    @pytest.mark.asyncio
    async def test_metadata_forwarded(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        bus.publish_inbound = AsyncMock()

        await ch._handle_message(
            "sender1", "chat1", "Hi", metadata={"reply_id": "123"}
        )
        msg = bus.publish_inbound.call_args[0][0]
        assert msg.metadata == {"reply_id": "123"}

    @pytest.mark.asyncio
    async def test_defaults_media_and_metadata(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        bus.publish_inbound = AsyncMock()

        await ch._handle_message("sender1", "chat1", "Hi")
        msg = bus.publish_inbound.call_args[0][0]
        assert msg.media == []
        assert msg.metadata == {}


class TestStartStop:
    """Tests for start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        await ch.start()
        assert ch.is_running is True

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, bus, config_no_allow):
        ch = ConcreteChannel(config_no_allow, bus)
        await ch.start()
        await ch.stop()
        assert ch.is_running is False


class TestAbstractEnforcement:
    """Tests that BaseChannel cannot be instantiated without implementing abstract methods."""

    def test_missing_start(self, bus, config_no_allow):
        class Incomplete(BaseChannel):
            name = "inc"
            async def stop(self): pass
            async def send(self, msg): pass

        with pytest.raises(TypeError):
            Incomplete(config_no_allow, bus)

    def test_missing_send(self, bus, config_no_allow):
        class Incomplete(BaseChannel):
            name = "inc"
            async def start(self): pass
            async def stop(self): pass

        with pytest.raises(TypeError):
            Incomplete(config_no_allow, bus)
