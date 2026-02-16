"""
Unit tests for Telegram channel (telegram.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-017
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from nanobot.channels.telegram import TelegramChannel, _markdown_to_telegram_html
from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus


class TestMarkdownToTelegramHtml:
    """Tests for _markdown_to_telegram_html() conversion."""

    def test_empty_string(self):
        assert _markdown_to_telegram_html("") == ""

    def test_none_returns_empty(self):
        assert _markdown_to_telegram_html(None) == ""

    def test_plain_text_unchanged(self):
        assert _markdown_to_telegram_html("Hello world") == "Hello world"

    def test_bold_asterisks(self):
        result = _markdown_to_telegram_html("**bold text**")
        assert "<b>bold text</b>" in result

    def test_bold_underscores(self):
        result = _markdown_to_telegram_html("__bold text__")
        assert "<b>bold text</b>" in result

    def test_italic(self):
        result = _markdown_to_telegram_html("_italic text_")
        assert "<i>italic text</i>" in result

    def test_strikethrough(self):
        result = _markdown_to_telegram_html("~~deleted~~")
        assert "<s>deleted</s>" in result

    def test_inline_code(self):
        result = _markdown_to_telegram_html("`some code`")
        assert "<code>some code</code>" in result

    def test_code_block(self):
        result = _markdown_to_telegram_html("```python\nprint('hi')\n```")
        assert "<pre><code>" in result
        assert "print" in result

    def test_html_escaping(self):
        result = _markdown_to_telegram_html("a < b > c & d")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_link_conversion(self):
        result = _markdown_to_telegram_html("[Google](https://google.com)")
        assert '<a href="https://google.com">Google</a>' in result

    def test_header_stripped(self):
        result = _markdown_to_telegram_html("# My Title")
        assert "#" not in result
        assert "My Title" in result

    def test_bullet_list(self):
        result = _markdown_to_telegram_html("- item one\n- item two")
        assert "item one" in result
        assert "item two" in result

    def test_blockquote_stripped(self):
        result = _markdown_to_telegram_html("> quoted text")
        assert "quoted text" in result

    def test_code_block_preserves_html_chars(self):
        result = _markdown_to_telegram_html("```\na < b && c > d\n```")
        assert "&lt;" in result
        assert "&amp;" in result


class TestTelegramChannelInit:
    """Tests for TelegramChannel initialization."""

    def test_name(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        assert ch.name == "telegram"

    def test_stores_groq_key(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus, groq_api_key="groq-123")
        assert ch.groq_api_key == "groq-123"

    def test_not_running_initially(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        assert ch.is_running is False


class TestTelegramGetExtension:
    """Tests for _get_extension() method."""

    def _make_channel(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        return TelegramChannel(config, bus)

    def test_jpeg_mime(self):
        ch = self._make_channel()
        assert ch._get_extension("image", "image/jpeg") == ".jpg"

    def test_png_mime(self):
        ch = self._make_channel()
        assert ch._get_extension("image", "image/png") == ".png"

    def test_ogg_mime(self):
        ch = self._make_channel()
        assert ch._get_extension("voice", "audio/ogg") == ".ogg"

    def test_fallback_by_type(self):
        ch = self._make_channel()
        assert ch._get_extension("voice", None) == ".ogg"
        assert ch._get_extension("image", None) == ".jpg"

    def test_unknown_type(self):
        ch = self._make_channel()
        assert ch._get_extension("unknown", None) == ""


class TestTelegramSend:
    """Tests for send() method."""

    @pytest.mark.asyncio
    async def test_send_without_app_does_nothing(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._app = None
        msg = OutboundMessage(channel="telegram", chat_id="123", content="Hi")
        # Should not raise
        await ch.send(msg)

    @pytest.mark.asyncio
    async def test_send_invalid_chat_id(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._app = MagicMock()
        ch._app.bot = MagicMock()
        msg = OutboundMessage(channel="telegram", chat_id="not-a-number", content="Hi")
        # Should handle ValueError gracefully
        await ch.send(msg)

    @pytest.mark.asyncio
    async def test_send_success(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._app = MagicMock()
        ch._app.bot = MagicMock()
        ch._app.bot.send_message = AsyncMock()
        ch._typing_tasks = {}
        msg = OutboundMessage(channel="telegram", chat_id="12345", content="Hello!")
        await ch.send(msg)
        ch._app.bot.send_message.assert_called_once()
        call_kwargs = ch._app.bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 12345
        assert call_kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_send_html_fallback_to_plain(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._app = MagicMock()
        ch._app.bot = MagicMock()
        # First call raises (HTML parse error), second succeeds
        ch._app.bot.send_message = AsyncMock(
            side_effect=[Exception("HTML parse error"), None]
        )
        ch._typing_tasks = {}
        msg = OutboundMessage(channel="telegram", chat_id="12345", content="Hello!")
        await ch.send(msg)
        assert ch._app.bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_send_both_fail(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._app = MagicMock()
        ch._app.bot = MagicMock()
        ch._app.bot.send_message = AsyncMock(side_effect=Exception("fail"))
        ch._typing_tasks = {}
        msg = OutboundMessage(channel="telegram", chat_id="12345", content="Hello!")
        # Should not raise
        await ch.send(msg)


class TestTelegramStop:
    """Tests for stop() method."""

    @pytest.mark.asyncio
    async def test_stop_without_app(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._running = True
        ch._app = None
        await ch.stop()
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_stop_with_app(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._running = True
        mock_app = MagicMock()
        mock_app.updater = MagicMock()
        mock_app.updater.stop = AsyncMock()
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()
        ch._app = mock_app
        ch._typing_tasks = {}
        await ch.stop()
        assert ch._running is False
        assert ch._app is None
        mock_app.updater.stop.assert_called_once()
        mock_app.stop.assert_called_once()
        mock_app.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_cancels_typing_tasks(self):
        import asyncio
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._running = True
        ch._app = None
        task = asyncio.create_task(asyncio.sleep(100))
        ch._typing_tasks = {"123": task}
        await ch.stop()
        await asyncio.sleep(0)  # let cancellation propagate
        assert ch._running is False
        assert task.cancelled()


class TestTelegramTyping:
    """Tests for typing indicator methods."""

    def test_stop_typing_removes_task(self):
        import asyncio
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        task = MagicMock()
        task.done.return_value = False
        ch._typing_tasks = {"123": task}
        ch._stop_typing("123")
        task.cancel.assert_called_once()
        assert "123" not in ch._typing_tasks

    def test_stop_typing_no_task(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._typing_tasks = {}
        ch._stop_typing("123")  # Should not raise

    def test_stop_typing_done_task(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        task = MagicMock()
        task.done.return_value = True
        ch._typing_tasks = {"123": task}
        ch._stop_typing("123")
        task.cancel.assert_not_called()

    def test_start_typing_creates_task(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._typing_tasks = {}
        with patch("asyncio.create_task") as mock_create:
            mock_create.return_value = MagicMock()
            ch._start_typing("123")
            mock_create.assert_called_once()
            assert "123" in ch._typing_tasks


class TestTelegramOnStart:
    """Tests for _on_start() command handler."""

    @pytest.mark.asyncio
    async def test_on_start_sends_greeting(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.first_name = "Alice"
        context = MagicMock()
        await ch._on_start(update, context)
        update.message.reply_text.assert_called_once()
        greeting = update.message.reply_text.call_args[0][0]
        assert "Alice" in greeting

    @pytest.mark.asyncio
    async def test_on_start_no_message(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = None
        update.effective_user = MagicMock()
        context = MagicMock()
        await ch._on_start(update, context)  # Should return early

    @pytest.mark.asyncio
    async def test_on_start_no_user(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = MagicMock()
        update.effective_user = None
        context = MagicMock()
        await ch._on_start(update, context)  # Should return early


class TestTelegramForwardCommand:
    """Tests for _forward_command()."""

    @pytest.mark.asyncio
    async def test_forward_command(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch.bus.publish_inbound = AsyncMock()
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "/help"
        update.message.chat_id = 999
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        context = MagicMock()
        await ch._forward_command(update, context)
        ch.bus.publish_inbound.assert_called_once()

    @pytest.mark.asyncio
    async def test_forward_command_no_message(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = None
        update.effective_user = MagicMock()
        context = MagicMock()
        await ch._forward_command(update, context)  # Should return early


class TestTelegramOnError:
    """Tests for _on_error()."""

    @pytest.mark.asyncio
    async def test_on_error_logs(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        context = MagicMock()
        context.error = Exception("test error")
        await ch._on_error(MagicMock(), context)  # Should not raise


class TestTelegramOnMessage:
    """Tests for _on_message() handler."""

    @pytest.mark.asyncio
    async def test_text_message(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.effective_user.username = "alice"
        update.effective_user.first_name = "Alice"

        message = MagicMock()
        message.chat_id = 999
        message.message_id = 1
        message.text = "Hello bot!"
        message.caption = None
        message.photo = None
        message.voice = None
        message.audio = None
        message.document = None
        message.chat = MagicMock()
        message.chat.type = "private"
        update.message = message

        with patch("asyncio.create_task"):
            await ch._on_message(update, MagicMock())

        ch.bus.publish_inbound.assert_called_once()
        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.content == "Hello bot!"
        assert "42" in msg.sender_id
        assert "alice" in msg.sender_id

    @pytest.mark.asyncio
    async def test_no_message(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = None
        update.effective_user = MagicMock()
        await ch._on_message(update, MagicMock())

    @pytest.mark.asyncio
    async def test_no_user(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        update = MagicMock()
        update.message = MagicMock()
        update.effective_user = None
        await ch._on_message(update, MagicMock())

    @pytest.mark.asyncio
    async def test_empty_message_placeholder(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.effective_user.username = None

        message = MagicMock()
        message.chat_id = 999
        message.message_id = 1
        message.text = None
        message.caption = None
        message.photo = None
        message.voice = None
        message.audio = None
        message.document = None
        message.chat = MagicMock()
        message.chat.type = "private"
        update.message = message

        with patch("asyncio.create_task"):
            await ch._on_message(update, MagicMock())

        msg = ch.bus.publish_inbound.call_args[0][0]
        assert msg.content == "[empty message]"

    @pytest.mark.asyncio
    async def test_caption_message(self):
        config = SimpleNamespace(token="fake", allow_from=[], proxy=None)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch.bus.publish_inbound = AsyncMock()
        ch._typing_tasks = {}

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.effective_user.username = None

        message = MagicMock()
        message.chat_id = 999
        message.message_id = 1
        message.text = None
        message.caption = "Photo caption"
        message.photo = None
        message.voice = None
        message.audio = None
        message.document = None
        message.chat = MagicMock()
        message.chat.type = "private"
        update.message = message

        with patch("asyncio.create_task"):
            await ch._on_message(update, MagicMock())

        msg = ch.bus.publish_inbound.call_args[0][0]
        assert "Photo caption" in msg.content
