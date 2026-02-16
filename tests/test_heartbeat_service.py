"""
Unit tests for heartbeat/service.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from nanobot.heartbeat.service import (
    HeartbeatService,
    _is_heartbeat_empty,
    HEARTBEAT_PROMPT,
    HEARTBEAT_OK_TOKEN,
    DEFAULT_HEARTBEAT_INTERVAL_S,
)


class TestIsHeartbeatEmpty:
    def test_none_is_empty(self):
        assert _is_heartbeat_empty(None) is True

    def test_empty_string_is_empty(self):
        assert _is_heartbeat_empty("") is True

    def test_only_headers_is_empty(self):
        assert _is_heartbeat_empty("# Tasks\n## Subtasks") is True

    def test_only_whitespace_is_empty(self):
        assert _is_heartbeat_empty("  \n  \n  ") is True

    def test_only_checkboxes_is_empty(self):
        assert _is_heartbeat_empty("- [ ]\n* [x]") is True

    def test_actionable_content(self):
        assert _is_heartbeat_empty("# Tasks\nSend daily report") is False

    def test_html_comment_only(self):
        assert _is_heartbeat_empty("<!-- placeholder -->") is True

    def test_mixed_content(self):
        assert _is_heartbeat_empty("# Title\n\nDo something\n- [ ]") is False


class TestHeartbeatServiceInit:
    def test_defaults(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path)
        assert svc.workspace == tmp_path
        assert svc.interval_s == DEFAULT_HEARTBEAT_INTERVAL_S
        assert svc.enabled is True
        assert svc._running is False

    def test_custom_interval(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, interval_s=60)
        assert svc.interval_s == 60

    def test_disabled(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, enabled=False)
        assert svc.enabled is False

    def test_heartbeat_file_path(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path)
        assert svc.heartbeat_file == tmp_path / "HEARTBEAT.md"


class TestReadHeartbeatFile:
    def test_file_not_exists(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path)
        assert svc._read_heartbeat_file() is None

    def test_file_exists(self, tmp_path):
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("# Tasks\nSend report")
        svc = HeartbeatService(workspace=tmp_path)
        content = svc._read_heartbeat_file()
        assert "Send report" in content


class TestHeartbeatStart:
    @pytest.mark.asyncio
    async def test_start_when_disabled(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, enabled=False)
        await svc.start()
        assert svc._running is False
        assert svc._task is None

    @pytest.mark.asyncio
    async def test_start_creates_task(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, interval_s=1)
        await svc.start()
        assert svc._running is True
        assert svc._task is not None
        svc.stop()


class TestHeartbeatStop:
    @pytest.mark.asyncio
    async def test_stop(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, interval_s=1)
        await svc.start()
        svc.stop()
        assert svc._running is False
        assert svc._task is None

    def test_stop_when_not_started(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path)
        svc.stop()  # Should not raise


class TestHeartbeatTick:
    @pytest.mark.asyncio
    async def test_tick_empty_file_skips(self, tmp_path):
        callback = AsyncMock()
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback)
        await svc._tick()
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_tick_with_content_calls_callback(self, tmp_path):
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("Send daily report")
        callback = AsyncMock(return_value="HEARTBEAT_OK")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback)
        await svc._tick()
        callback.assert_called_once_with(HEARTBEAT_PROMPT)

    @pytest.mark.asyncio
    async def test_tick_callback_error(self, tmp_path):
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("Do something")
        callback = AsyncMock(side_effect=Exception("fail"))
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback)
        await svc._tick()  # Should not raise

    @pytest.mark.asyncio
    async def test_tick_no_callback(self, tmp_path):
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("Some task")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=None)
        await svc._tick()  # Should not raise


class TestTriggerNow:
    @pytest.mark.asyncio
    async def test_trigger_with_callback(self, tmp_path):
        callback = AsyncMock(return_value="done")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback)
        result = await svc.trigger_now()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_trigger_without_callback(self, tmp_path):
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=None)
        result = await svc.trigger_now()
        assert result is None


class TestHeartbeatRunLoop:
    @pytest.mark.asyncio
    async def test_run_loop_executes_tick(self, tmp_path):
        """Test that the run loop calls _tick after sleep."""
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("Do something")
        callback = AsyncMock(return_value="HEARTBEAT_OK")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback, interval_s=0.01)
        svc._running = True
        task = asyncio.create_task(svc._run_loop())
        await asyncio.sleep(0.05)
        svc._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert callback.call_count >= 1

    @pytest.mark.asyncio
    async def test_run_loop_handles_exception(self, tmp_path):
        """Test that _run_loop continues after _tick raises."""
        callback = AsyncMock(side_effect=Exception("boom"))
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("task")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback, interval_s=0.01)
        svc._running = True
        task = asyncio.create_task(svc._run_loop())
        await asyncio.sleep(0.05)
        svc._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestHeartbeatReadFileError:
    def test_read_file_exception(self, tmp_path):
        """Cover the except branch in _read_heartbeat_file."""
        from unittest.mock import patch
        svc = HeartbeatService(workspace=tmp_path)
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("content")
        with patch.object(Path, "read_text", side_effect=OSError("read error")):
            result = svc._read_heartbeat_file()
        assert result is None


class TestHeartbeatTickCompletedTask:
    @pytest.mark.asyncio
    async def test_tick_completed_task(self, tmp_path):
        """Cover line 125: response that isn't HEARTBEAT_OK."""
        hb_file = tmp_path / "HEARTBEAT.md"
        hb_file.write_text("Send daily report")
        callback = AsyncMock(return_value="I sent the report successfully.")
        svc = HeartbeatService(workspace=tmp_path, on_heartbeat=callback)
        await svc._tick()  # Should log "completed task"
        callback.assert_called_once()


class TestConstants:
    def test_default_interval(self):
        assert DEFAULT_HEARTBEAT_INTERVAL_S == 30 * 60

    def test_ok_token(self):
        assert "HEARTBEAT" in HEARTBEAT_OK_TOKEN
