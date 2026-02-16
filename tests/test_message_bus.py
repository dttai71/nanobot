"""
Unit tests for MessageBus (nanobot/bus/).

Stage: 05 - TEST
Sprint: Sprint 01 - TT-006
"""

import asyncio
import pytest

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


# --- InboundMessage tests ---

class TestInboundMessage:
    def test_session_key(self):
        msg = InboundMessage(
            channel="telegram", sender_id="user1", chat_id="12345", content="hello"
        )
        assert msg.session_key == "telegram:12345"

    def test_session_key_with_colon_in_chat_id(self):
        msg = InboundMessage(
            channel="slack", sender_id="u1", chat_id="C01:thread1", content="hi"
        )
        assert msg.session_key == "slack:C01:thread1"

    def test_default_fields(self):
        msg = InboundMessage(
            channel="discord", sender_id="u1", chat_id="c1", content="test"
        )
        assert msg.media == []
        assert msg.metadata == {}
        assert msg.timestamp is not None

    def test_media_and_metadata(self):
        msg = InboundMessage(
            channel="telegram",
            sender_id="u1",
            chat_id="c1",
            content="photo",
            media=["https://example.com/img.jpg"],
            metadata={"message_id": 42},
        )
        assert len(msg.media) == 1
        assert msg.metadata["message_id"] == 42


class TestOutboundMessage:
    def test_basic_creation(self):
        msg = OutboundMessage(channel="telegram", chat_id="12345", content="response")
        assert msg.channel == "telegram"
        assert msg.chat_id == "12345"
        assert msg.content == "response"
        assert msg.reply_to is None

    def test_reply_to(self):
        msg = OutboundMessage(
            channel="slack", chat_id="C01", content="reply", reply_to="msg123"
        )
        assert msg.reply_to == "msg123"


# --- MessageBus tests ---

class TestMessageBus:
    @pytest.fixture
    def bus(self):
        return MessageBus()

    async def test_publish_and_consume_inbound(self, bus):
        msg = InboundMessage(
            channel="telegram", sender_id="u1", chat_id="c1", content="hello"
        )
        await bus.publish_inbound(msg)
        assert bus.inbound_size == 1

        received = await bus.consume_inbound()
        assert received.content == "hello"
        assert received.channel == "telegram"
        assert bus.inbound_size == 0

    async def test_publish_and_consume_outbound(self, bus):
        msg = OutboundMessage(channel="discord", chat_id="c1", content="response")
        await bus.publish_outbound(msg)
        assert bus.outbound_size == 1

        received = await bus.consume_outbound()
        assert received.content == "response"
        assert bus.outbound_size == 0

    async def test_fifo_ordering(self, bus):
        for i in range(5):
            await bus.publish_inbound(
                InboundMessage(
                    channel="test", sender_id="u1", chat_id="c1", content=f"msg-{i}"
                )
            )
        assert bus.inbound_size == 5

        for i in range(5):
            msg = await bus.consume_inbound()
            assert msg.content == f"msg-{i}"

    async def test_subscribe_and_dispatch(self, bus):
        received_messages = []

        async def callback(msg: OutboundMessage):
            received_messages.append(msg)

        bus.subscribe_outbound("telegram", callback)

        await bus.publish_outbound(
            OutboundMessage(channel="telegram", chat_id="c1", content="dispatched")
        )

        # Run dispatch in background, let it process one message
        task = asyncio.create_task(bus.dispatch_outbound())
        await asyncio.sleep(0.1)
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(received_messages) == 1
        assert received_messages[0].content == "dispatched"

    async def test_dispatch_routes_to_correct_channel(self, bus):
        telegram_msgs = []
        discord_msgs = []

        async def telegram_cb(msg):
            telegram_msgs.append(msg)

        async def discord_cb(msg):
            discord_msgs.append(msg)

        bus.subscribe_outbound("telegram", telegram_cb)
        bus.subscribe_outbound("discord", discord_cb)

        await bus.publish_outbound(
            OutboundMessage(channel="telegram", chat_id="t1", content="for telegram")
        )
        await bus.publish_outbound(
            OutboundMessage(channel="discord", chat_id="d1", content="for discord")
        )

        task = asyncio.create_task(bus.dispatch_outbound())
        await asyncio.sleep(0.2)
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(telegram_msgs) == 1
        assert telegram_msgs[0].content == "for telegram"
        assert len(discord_msgs) == 1
        assert discord_msgs[0].content == "for discord"

    async def test_dispatch_unsubscribed_channel_no_error(self, bus):
        """Messages to channels with no subscribers should not raise."""
        await bus.publish_outbound(
            OutboundMessage(channel="unknown", chat_id="c1", content="orphan")
        )

        task = asyncio.create_task(bus.dispatch_outbound())
        await asyncio.sleep(0.1)
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        # No exception = success

    async def test_dispatch_callback_error_handled(self, bus):
        """Errors in callbacks should not crash the dispatcher."""
        good_msgs = []

        async def failing_cb(msg):
            raise RuntimeError("callback failed")

        async def good_cb(msg):
            good_msgs.append(msg)

        bus.subscribe_outbound("test", failing_cb)
        bus.subscribe_outbound("test", good_cb)

        await bus.publish_outbound(
            OutboundMessage(channel="test", chat_id="c1", content="test")
        )

        task = asyncio.create_task(bus.dispatch_outbound())
        await asyncio.sleep(0.1)
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Good callback should still receive the message despite failing sibling
        assert len(good_msgs) == 1

    async def test_multiple_subscribers_same_channel(self, bus):
        results_a = []
        results_b = []

        async def cb_a(msg):
            results_a.append(msg)

        async def cb_b(msg):
            results_b.append(msg)

        bus.subscribe_outbound("telegram", cb_a)
        bus.subscribe_outbound("telegram", cb_b)

        await bus.publish_outbound(
            OutboundMessage(channel="telegram", chat_id="c1", content="broadcast")
        )

        task = asyncio.create_task(bus.dispatch_outbound())
        await asyncio.sleep(0.1)
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_initial_state(self, bus):
        assert bus.inbound_size == 0
        assert bus.outbound_size == 0
        assert bus._running is False

    def test_stop(self, bus):
        bus._running = True
        bus.stop()
        assert bus._running is False
