"""
Unit tests for Discord channel (discord.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-018
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from nanobot.channels.discord import DiscordChannel, DISCORD_API_BASE, MAX_ATTACHMENT_BYTES
from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus


def _make_config(**overrides):
    defaults = dict(
        enabled=False, token="fake-token", allow_from=[],
        gateway_url="wss://gateway.discord.gg/?v=10&encoding=json",
        intents=37377,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestDiscordChannelInit:
    """Tests for DiscordChannel initialization."""

    def test_name(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        assert ch.name == "discord"

    def test_not_running_initially(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        assert ch.is_running is False
        assert ch._ws is None
        assert ch._seq is None


class TestDiscordStop:
    """Tests for stop() cleanup."""

    @pytest.mark.asyncio
    async def test_stop_clears_state(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True
        ch._heartbeat_task = None
        ch._ws = None
        ch._http = None
        await ch.stop()
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_heartbeat(self):
        import asyncio
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True
        ch._heartbeat_task = asyncio.create_task(asyncio.sleep(100))
        ch._ws = None
        ch._http = None
        await ch.stop()
        assert ch._heartbeat_task is None


class TestDiscordSend:
    """Tests for send() method."""

    @pytest.mark.asyncio
    async def test_send_without_http_does_nothing(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._http = None
        msg = OutboundMessage(channel="discord", chat_id="123", content="Hi")
        await ch.send(msg)

    @pytest.mark.asyncio
    async def test_send_posts_to_api(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        ch._http = mock_http
        ch._typing_tasks = {}

        msg = OutboundMessage(channel="discord", chat_id="456", content="Hello!")
        await ch.send(msg)

        mock_http.post.assert_called()
        call_args = mock_http.post.call_args
        assert "/channels/456/messages" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_with_reply_to(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        ch._http = mock_http
        ch._typing_tasks = {}

        msg = OutboundMessage(
            channel="discord", chat_id="456", content="Reply!",
            reply_to="789"
        )
        await ch.send(msg)
        call_kwargs = mock_http.post.call_args
        payload = call_kwargs[1]["json"]
        assert "message_reference" in payload
        assert payload["message_reference"]["message_id"] == "789"


class TestDiscordHandleMessageCreate:
    """Tests for _handle_message_create() message parsing."""

    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()

        payload = {
            "author": {"id": "bot-1", "bot": True},
            "channel_id": "ch-1",
            "content": "Bot message",
        }
        await ch._handle_message_create(payload)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_empty_sender(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()

        payload = {
            "author": {"id": ""},
            "channel_id": "ch-1",
            "content": "Hello",
        }
        await ch._handle_message_create(payload)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_parses_text_message(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        payload = {
            "id": "msg-1",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "Hello Discord!",
            "guild_id": "g-1",
        }
        await ch._handle_message_create(payload)
        ch.bus.publish_inbound.assert_called_once()
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.content == "Hello Discord!"
        assert msg.sender_id == "user-1"
        assert msg.channel == "discord"

    @pytest.mark.asyncio
    async def test_empty_content_becomes_placeholder(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        payload = {
            "id": "msg-2",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "",
        }
        await ch._handle_message_create(payload)
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.content == "[empty message]"


class TestDiscordStopTyping:
    """Tests for _stop_typing() and _start_typing()."""

    @pytest.mark.asyncio
    async def test_stop_typing_cancels_task(self):
        import asyncio
        ch = DiscordChannel(_make_config(), MessageBus())
        task = asyncio.create_task(asyncio.sleep(100))
        ch._typing_tasks = {"ch-1": task}
        await ch._stop_typing("ch-1")
        await asyncio.sleep(0)  # let cancellation propagate
        assert "ch-1" not in ch._typing_tasks
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_typing_no_task(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._typing_tasks = {}
        await ch._stop_typing("ch-1")  # Should not raise


class TestDiscordIdentify:
    """Tests for _identify()."""

    @pytest.mark.asyncio
    async def test_identify_sends_payload(self):
        import json
        ch = DiscordChannel(_make_config(token="test-token", intents=37377), MessageBus())
        mock_ws = AsyncMock()
        ch._ws = mock_ws
        await ch._identify()
        mock_ws.send.assert_called_once()
        payload = json.loads(mock_ws.send.call_args[0][0])
        assert payload["op"] == 2
        assert payload["d"]["token"] == "test-token"
        assert payload["d"]["intents"] == 37377

    @pytest.mark.asyncio
    async def test_identify_without_ws(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._ws = None
        await ch._identify()  # Should return early


class TestDiscordStartHeartbeat:
    """Tests for _start_heartbeat()."""

    @pytest.mark.asyncio
    async def test_start_heartbeat_creates_task(self):
        import asyncio
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True
        ch._ws = AsyncMock()
        await ch._start_heartbeat(1.0)
        assert ch._heartbeat_task is not None
        ch._heartbeat_task.cancel()
        try:
            await ch._heartbeat_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_start_heartbeat_cancels_previous(self):
        import asyncio
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True
        ch._ws = AsyncMock()
        old_task = asyncio.create_task(asyncio.sleep(100))
        ch._heartbeat_task = old_task
        await ch._start_heartbeat(1.0)
        await asyncio.sleep(0)  # let cancellation propagate
        assert old_task.cancelled()
        ch._heartbeat_task.cancel()
        try:
            await ch._heartbeat_task
        except asyncio.CancelledError:
            pass


class TestDiscordHandleMessageCreateAttachments:
    """Tests for _handle_message_create() with attachments."""

    @pytest.mark.asyncio
    async def test_too_large_attachment(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}
        ch._http = AsyncMock()

        payload = {
            "id": "msg-1",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "See file",
            "attachments": [
                {"id": "a1", "url": "https://cdn.discord.com/file.bin",
                 "filename": "huge.bin", "size": MAX_ATTACHMENT_BYTES + 1}
            ],
        }
        await ch._handle_message_create(payload)
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert "too large" in msg.content

    @pytest.mark.asyncio
    async def test_attachment_download_success(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}
        mock_resp = MagicMock()
        mock_resp.content = b"file-data"
        mock_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        ch._http = mock_http

        payload = {
            "id": "msg-1",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "",
            "attachments": [
                {"id": "a1", "url": "https://cdn.discord.com/file.txt",
                 "filename": "test.txt", "size": 100}
            ],
        }
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"):
            await ch._handle_message_create(payload)
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert "attachment" in msg.content

    @pytest.mark.asyncio
    async def test_attachment_download_failure(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("network error"))
        ch._http = mock_http

        payload = {
            "id": "msg-1",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "See file",
            "attachments": [
                {"id": "a1", "url": "https://cdn.discord.com/file.txt",
                 "filename": "test.txt", "size": 100}
            ],
        }
        with patch("pathlib.Path.mkdir"):
            await ch._handle_message_create(payload)
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert "download failed" in msg.content

    @pytest.mark.asyncio
    async def test_reply_to_included(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch.bus = MagicMock()
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        payload = {
            "id": "msg-1",
            "author": {"id": "user-1"},
            "channel_id": "ch-1",
            "content": "replying",
            "referenced_message": {"id": "orig-msg-1"},
        }
        await ch._handle_message_create(payload)
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.metadata.get("reply_to") == "orig-msg-1"


class TestDiscordSendRetry:
    """Tests for send() retry logic."""

    @pytest.mark.asyncio
    async def test_send_rate_limited_retries(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        rate_resp = MagicMock()
        rate_resp.status_code = 429
        rate_resp.json.return_value = {"retry_after": 0.01}
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=[rate_resp, ok_resp])
        ch._http = mock_http
        ch._typing_tasks = {}

        msg = OutboundMessage(channel="discord", chat_id="123", content="Hi")
        await ch.send(msg)
        assert mock_http.post.call_count == 2

    @pytest.mark.asyncio
    async def test_send_all_retries_fail(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=Exception("fail"))
        ch._http = mock_http
        ch._typing_tasks = {}

        msg = OutboundMessage(channel="discord", chat_id="123", content="Hi")
        await ch.send(msg)  # Should not raise


class _AsyncIter:
    """Helper to create an async iterator from a list of items."""
    def __init__(self, items):
        self._items = iter(items)
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


class TestDiscordGatewayLoop:
    """Tests for _gateway_loop() event handling."""

    @pytest.mark.asyncio
    async def test_gateway_loop_hello_event(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        hello_msg = json.dumps({
            "op": 10, "d": {"heartbeat_interval": 41250},
            "s": None, "t": None
        })
        ch._ws = _AsyncIter([hello_msg])

        with patch.object(ch, "_start_heartbeat", new_callable=AsyncMock) as mock_hb, \
             patch.object(ch, "_identify", new_callable=AsyncMock) as mock_id:
            await ch._gateway_loop()
            mock_hb.assert_called_once()
            mock_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_loop_message_create(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        msg_data = json.dumps({
            "op": 0, "t": "MESSAGE_CREATE", "s": 1,
            "d": {"author": {"id": "u1"}, "channel_id": "c1", "content": "hi"}
        })
        ch._ws = _AsyncIter([msg_data])

        with patch.object(ch, "_handle_message_create", new_callable=AsyncMock) as mock_handle:
            await ch._gateway_loop()
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_loop_reconnect(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        reconnect_msg = json.dumps({"op": 7, "d": None, "s": None, "t": None})
        ch._ws = _AsyncIter([reconnect_msg])
        await ch._gateway_loop()  # Should break out of loop

    @pytest.mark.asyncio
    async def test_gateway_loop_invalid_session(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        msg = json.dumps({"op": 9, "d": False, "s": None, "t": None})
        ch._ws = _AsyncIter([msg])
        await ch._gateway_loop()  # Should break

    @pytest.mark.asyncio
    async def test_gateway_loop_invalid_json(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        ch._ws = _AsyncIter(["not-json{{}"])
        await ch._gateway_loop()  # Should skip invalid JSON

    @pytest.mark.asyncio
    async def test_gateway_loop_no_ws(self):
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._ws = None
        await ch._gateway_loop()  # Should return early

    @pytest.mark.asyncio
    async def test_gateway_loop_ready_event(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True

        ready_msg = json.dumps({"op": 0, "t": "READY", "s": 1, "d": {}})
        ch._ws = _AsyncIter([ready_msg])
        await ch._gateway_loop()  # Just logs, no action

    @pytest.mark.asyncio
    async def test_gateway_loop_sequence_tracking(self):
        import json
        ch = DiscordChannel(_make_config(), MessageBus())
        ch._running = True
        assert ch._seq is None

        msg = json.dumps({"op": 0, "t": "READY", "s": 42, "d": {}})
        ch._ws = _AsyncIter([msg])
        await ch._gateway_loop()
        assert ch._seq == 42


class TestDiscordConstants:
    """Tests for module-level constants."""

    def test_api_base(self):
        assert "discord.com" in DISCORD_API_BASE

    def test_max_attachment_size(self):
        assert MAX_ATTACHMENT_BYTES == 20 * 1024 * 1024
