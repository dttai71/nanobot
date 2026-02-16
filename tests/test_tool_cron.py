"""
Unit tests for agent/tools/cron.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import MagicMock, patch

from nanobot.agent.tools.cron import CronTool
from nanobot.cron.service import CronService
from nanobot.cron.types import CronJob, CronSchedule, CronJobState


def _make_mock_service(tmp_path):
    """Create a CronService with a temp store path."""
    return CronService(store_path=tmp_path / "cron.json")


class TestCronToolInit:
    def test_init(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        assert tool._cron is svc
        assert tool._channel == ""
        assert tool._chat_id == ""

    def test_properties(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        assert tool.name == "cron"
        assert "schedule" in tool.description.lower() or "remind" in tool.description.lower()
        assert tool.parameters["type"] == "object"
        assert "action" in tool.parameters["properties"]

    def test_set_context(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        assert tool._channel == "telegram"
        assert tool._chat_id == "12345"


class TestCronToolExecute:
    @pytest.mark.asyncio
    async def test_add_every(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        result = await tool.execute(action="add", message="Check status", every_seconds=60)
        assert "created" in result.lower()

    @pytest.mark.asyncio
    async def test_add_cron_expr(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        result = await tool.execute(action="add", message="Morning check", cron_expr="0 9 * * *")
        assert "created" in result.lower()

    @pytest.mark.asyncio
    async def test_add_at(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        result = await tool.execute(action="add", message="One time", at="2099-12-31T23:59:00")
        assert "created" in result.lower()

    @pytest.mark.asyncio
    async def test_add_no_message(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        result = await tool.execute(action="add", every_seconds=60)
        assert "error" in result.lower()
        assert "message" in result.lower()

    @pytest.mark.asyncio
    async def test_add_no_context(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        result = await tool.execute(action="add", message="test", every_seconds=60)
        assert "error" in result.lower()
        assert "context" in result.lower()

    @pytest.mark.asyncio
    async def test_add_no_schedule(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        tool.set_context("telegram", "12345")
        result = await tool.execute(action="add", message="test")
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_list_empty(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        result = await tool.execute(action="list")
        assert "no scheduled" in result.lower()

    @pytest.mark.asyncio
    async def test_list_with_jobs(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        svc.add_job("Test Job", CronSchedule(kind="every", every_ms=60000), "msg")
        tool = CronTool(svc)
        result = await tool.execute(action="list")
        assert "Test Job" in result

    @pytest.mark.asyncio
    async def test_remove_success(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        job = svc.add_job("To Remove", CronSchedule(kind="every", every_ms=60000), "msg")
        tool = CronTool(svc)
        result = await tool.execute(action="remove", job_id=job.id)
        assert "removed" in result.lower()

    @pytest.mark.asyncio
    async def test_remove_not_found(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        result = await tool.execute(action="remove", job_id="fake-id")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_remove_no_id(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        result = await tool.execute(action="remove")
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self, tmp_path):
        svc = _make_mock_service(tmp_path)
        tool = CronTool(svc)
        result = await tool.execute(action="unknown")
        assert "unknown" in result.lower()
