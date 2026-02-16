"""
Unit tests for Slack channel (slack.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-019
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus


def _make_slack_config(**overrides):
    defaults = dict(
        enabled=False,
        mode="socket",
        webhook_path="/slack/events",
        bot_token="xoxb-fake",
        app_token="xapp-fake",
        user_token_read_only=True,
        group_policy="mention",
        group_allow_from=[],
        dm=SimpleNamespace(enabled=True, policy="open", allow_from=[]),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# Patch imports at module level to avoid requiring slack_sdk
@pytest.fixture
def slack_channel_class():
    """Import SlackChannel with mocked slack_sdk dependencies."""
    with patch.dict("sys.modules", {
        "slack_sdk": MagicMock(),
        "slack_sdk.socket_mode": MagicMock(),
        "slack_sdk.socket_mode.websockets": MagicMock(),
        "slack_sdk.socket_mode.request": MagicMock(),
        "slack_sdk.socket_mode.response": MagicMock(),
        "slack_sdk.web": MagicMock(),
        "slack_sdk.web.async_client": MagicMock(),
    }):
        from nanobot.channels.slack import SlackChannel
        return SlackChannel


class TestSlackChannelInit:
    """Tests for SlackChannel initialization."""

    def test_name(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        assert ch.name == "slack"

    def test_not_running_initially(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        assert ch.is_running is False
        assert ch._web_client is None
        assert ch._socket_client is None
        assert ch._bot_user_id is None


class TestSlackStripBotMention:
    """Tests for _strip_bot_mention() helper."""

    def test_strips_mention(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "U12345"
        result = ch._strip_bot_mention("<@U12345> hello bot")
        assert result == "hello bot"

    def test_no_mention(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "U12345"
        result = ch._strip_bot_mention("just a message")
        assert result == "just a message"

    def test_no_bot_id(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = None
        result = ch._strip_bot_mention("<@U12345> hello")
        assert result == "<@U12345> hello"

    def test_empty_text(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "U12345"
        assert ch._strip_bot_mention("") == ""

    def test_none_text(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "U12345"
        assert ch._strip_bot_mention(None) is None


class TestSlackIsAllowed:
    """Tests for _is_allowed() access control."""

    def test_dm_open_policy_allows_all(self, slack_channel_class):
        config = _make_slack_config(
            dm=SimpleNamespace(enabled=True, policy="open", allow_from=[])
        )
        ch = slack_channel_class(config, MessageBus())
        assert ch._is_allowed("U99", "C99", "im") is True

    def test_dm_disabled_denies(self, slack_channel_class):
        config = _make_slack_config(
            dm=SimpleNamespace(enabled=False, policy="open", allow_from=[])
        )
        ch = slack_channel_class(config, MessageBus())
        assert ch._is_allowed("U99", "C99", "im") is False

    def test_dm_allowlist_policy(self, slack_channel_class):
        config = _make_slack_config(
            dm=SimpleNamespace(enabled=True, policy="allowlist", allow_from=["U1"])
        )
        ch = slack_channel_class(config, MessageBus())
        assert ch._is_allowed("U1", "C99", "im") is True
        assert ch._is_allowed("U2", "C99", "im") is False

    def test_group_allowlist_policy(self, slack_channel_class):
        config = _make_slack_config(
            group_policy="allowlist", group_allow_from=["C1"]
        )
        ch = slack_channel_class(config, MessageBus())
        assert ch._is_allowed("U1", "C1", "channel") is True
        assert ch._is_allowed("U1", "C2", "channel") is False

    def test_group_open_policy(self, slack_channel_class):
        config = _make_slack_config(group_policy="open")
        ch = slack_channel_class(config, MessageBus())
        assert ch._is_allowed("U1", "C1", "channel") is True


class TestSlackShouldRespondInChannel:
    """Tests for _should_respond_in_channel()."""

    def test_open_policy(self, slack_channel_class):
        config = _make_slack_config(group_policy="open")
        ch = slack_channel_class(config, MessageBus())
        assert ch._should_respond_in_channel("message", "hello", "C1") is True

    def test_mention_policy_app_mention(self, slack_channel_class):
        config = _make_slack_config(group_policy="mention")
        ch = slack_channel_class(config, MessageBus())
        assert ch._should_respond_in_channel("app_mention", "hello", "C1") is True

    def test_mention_policy_with_mention_text(self, slack_channel_class):
        config = _make_slack_config(group_policy="mention")
        ch = slack_channel_class(config, MessageBus())
        ch._bot_user_id = "U12345"
        assert ch._should_respond_in_channel("message", "<@U12345> hi", "C1") is True

    def test_mention_policy_no_mention(self, slack_channel_class):
        config = _make_slack_config(group_policy="mention")
        ch = slack_channel_class(config, MessageBus())
        ch._bot_user_id = "U12345"
        assert ch._should_respond_in_channel("message", "hello", "C1") is False

    def test_allowlist_policy(self, slack_channel_class):
        config = _make_slack_config(
            group_policy="allowlist", group_allow_from=["C1"]
        )
        ch = slack_channel_class(config, MessageBus())
        assert ch._should_respond_in_channel("message", "hello", "C1") is True
        assert ch._should_respond_in_channel("message", "hello", "C2") is False


class TestSlackSend:
    """Tests for send() method."""

    @pytest.mark.asyncio
    async def test_send_without_client_does_nothing(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._web_client = None
        msg = OutboundMessage(channel="slack", chat_id="C1", content="Hi")
        await ch.send(msg)

    @pytest.mark.asyncio
    async def test_send_calls_chat_post_message(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        mock_client = AsyncMock()
        ch._web_client = mock_client

        msg = OutboundMessage(
            channel="slack", chat_id="C1", content="Hello Slack!",
            metadata={"slack": {"thread_ts": "123.456", "channel_type": "channel"}}
        )
        await ch.send(msg)
        mock_client.chat_postMessage.assert_called_once()
        call_kwargs = mock_client.chat_postMessage.call_args[1]
        assert call_kwargs["channel"] == "C1"
        assert call_kwargs["text"] == "Hello Slack!"
        assert call_kwargs["thread_ts"] == "123.456"

    @pytest.mark.asyncio
    async def test_send_dm_no_thread(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        mock_client = AsyncMock()
        ch._web_client = mock_client

        msg = OutboundMessage(
            channel="slack", chat_id="D1", content="DM!",
            metadata={"slack": {"thread_ts": "123.456", "channel_type": "im"}}
        )
        await ch.send(msg)
        call_kwargs = mock_client.chat_postMessage.call_args[1]
        assert call_kwargs["thread_ts"] is None  # DMs don't use threads

    @pytest.mark.asyncio
    async def test_send_no_metadata(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        mock_client = AsyncMock()
        ch._web_client = mock_client

        msg = OutboundMessage(channel="slack", chat_id="C1", content="Hi!")
        await ch.send(msg)
        mock_client.chat_postMessage.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_error_logged(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        mock_client = AsyncMock()
        mock_client.chat_postMessage = AsyncMock(side_effect=Exception("api error"))
        ch._web_client = mock_client

        msg = OutboundMessage(channel="slack", chat_id="C1", content="Hi!")
        await ch.send(msg)  # Should not raise


class TestSlackStop:
    """Tests for stop() method."""

    @pytest.mark.asyncio
    async def test_stop_without_client(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._running = True
        ch._socket_client = None
        await ch.stop()
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_stop_with_client(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._running = True
        mock_socket = AsyncMock()
        ch._socket_client = mock_socket
        await ch.stop()
        assert ch._running is False
        assert ch._socket_client is None
        mock_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_close_error(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._running = True
        mock_socket = AsyncMock()
        mock_socket.close = AsyncMock(side_effect=Exception("close error"))
        ch._socket_client = mock_socket
        await ch.stop()  # Should not raise
        assert ch._socket_client is None


class TestSlackOnSocketRequest:
    """Tests for _on_socket_request() event handling."""

    @pytest.mark.asyncio
    async def test_ignores_non_events_api(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "interactive"
        req.envelope_id = "env-1"
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_non_message_events(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {"event": {"type": "reaction_added", "user": "U1", "channel": "C1"}}
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_subtype_messages(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {"type": "message", "subtype": "channel_join", "user": "U1", "channel": "C1"}
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_bot_own_messages(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "UBOT"
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {"type": "message", "user": "UBOT", "channel": "C1", "text": "hi"}
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_message_with_bot_mention(self, slack_channel_class):
        """Slack sends both message and app_mention for mentions. Skip message to avoid double."""
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch._bot_user_id = "UBOT"
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {
                "type": "message", "user": "U1", "channel": "C1",
                "text": "<@UBOT> hello", "channel_type": "channel"
            }
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_dm_message(self, slack_channel_class):
        config = _make_slack_config(
            dm=SimpleNamespace(enabled=True, policy="open", allow_from=[])
        )
        ch = slack_channel_class(config, MessageBus())
        ch._bot_user_id = "UBOT"
        ch._web_client = AsyncMock()
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {
                "type": "message", "user": "U1", "channel": "D1",
                "text": "hello bot", "channel_type": "im", "ts": "123.456"
            }
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_called_once()
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.content == "hello bot"
        assert msg.sender_id == "U1"

    @pytest.mark.asyncio
    async def test_handles_app_mention(self, slack_channel_class):
        config = _make_slack_config(group_policy="mention")
        ch = slack_channel_class(config, MessageBus())
        ch._bot_user_id = "UBOT"
        ch._web_client = AsyncMock()
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {
                "type": "app_mention", "user": "U1", "channel": "C1",
                "text": "<@UBOT> do something", "channel_type": "channel", "ts": "123.456"
            }
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_called_once()
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert "do something" in msg.content

    @pytest.mark.asyncio
    async def test_no_sender_id(self, slack_channel_class):
        ch = slack_channel_class(_make_slack_config(), MessageBus())
        ch.bus.publish_inbound = AsyncMock()
        client = AsyncMock()
        req = MagicMock()
        req.type = "events_api"
        req.envelope_id = "env-1"
        req.payload = {
            "event": {"type": "message", "user": None, "channel": "C1", "text": "hi"}
        }
        await ch._on_socket_request(client, req)
        ch.bus.publish_inbound.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_group_policy_denies(self, slack_channel_class):
        config = _make_slack_config(group_policy="unknown_policy")
        ch = slack_channel_class(config, MessageBus())
        assert ch._should_respond_in_channel("message", "hello", "C1") is False
