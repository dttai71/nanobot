"""
Unit tests for cron/service.py and cron/types.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from nanobot.cron.types import CronJob, CronJobState, CronPayload, CronSchedule, CronStore
from nanobot.cron.service import CronService, _compute_next_run, _now_ms


class TestCronTypes:
    """Tests for cron/types.py dataclasses."""

    def test_cron_schedule_at(self):
        s = CronSchedule(kind="at", at_ms=1000)
        assert s.kind == "at"
        assert s.at_ms == 1000

    def test_cron_schedule_every(self):
        s = CronSchedule(kind="every", every_ms=60000)
        assert s.every_ms == 60000

    def test_cron_schedule_cron(self):
        s = CronSchedule(kind="cron", expr="0 9 * * *", tz="UTC")
        assert s.expr == "0 9 * * *"

    def test_cron_payload_defaults(self):
        p = CronPayload()
        assert p.kind == "agent_turn"
        assert p.message == ""
        assert p.deliver is False

    def test_cron_job_state(self):
        s = CronJobState(next_run_at_ms=1000, last_status="ok")
        assert s.next_run_at_ms == 1000
        assert s.last_error is None

    def test_cron_job(self):
        job = CronJob(id="abc", name="test_job")
        assert job.id == "abc"
        assert job.enabled is True
        assert job.delete_after_run is False

    def test_cron_store(self):
        store = CronStore()
        assert store.version == 1
        assert store.jobs == []


class TestComputeNextRun:
    def test_at_future(self):
        now = _now_ms()
        result = _compute_next_run(CronSchedule(kind="at", at_ms=now + 10000), now)
        assert result == now + 10000

    def test_at_past(self):
        now = _now_ms()
        result = _compute_next_run(CronSchedule(kind="at", at_ms=now - 1000), now)
        assert result is None

    def test_every(self):
        now = _now_ms()
        result = _compute_next_run(CronSchedule(kind="every", every_ms=5000), now)
        assert result == now + 5000

    def test_every_zero(self):
        result = _compute_next_run(CronSchedule(kind="every", every_ms=0), _now_ms())
        assert result is None

    def test_every_negative(self):
        result = _compute_next_run(CronSchedule(kind="every", every_ms=-1), _now_ms())
        assert result is None

    def test_every_none(self):
        result = _compute_next_run(CronSchedule(kind="every"), _now_ms())
        assert result is None

    def test_cron_expr(self):
        pytest.importorskip("croniter")
        now = _now_ms()
        result = _compute_next_run(
            CronSchedule(kind="cron", expr="* * * * *"),  # every minute
            now
        )
        assert result is not None
        assert result > now

    def test_cron_invalid_expr(self):
        result = _compute_next_run(
            CronSchedule(kind="cron", expr="invalid"),
            _now_ms()
        )
        assert result is None

    def test_cron_no_expr(self):
        result = _compute_next_run(CronSchedule(kind="cron"), _now_ms())
        assert result is None

    def test_unknown_kind(self):
        result = _compute_next_run(CronSchedule(kind="unknown"), _now_ms())
        assert result is None


class TestCronServiceInit:
    def test_init(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        assert svc._running is False
        assert svc._store is None


class TestCronServiceLoadStore:
    def test_empty_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        store = svc._load_store()
        assert isinstance(store, CronStore)
        assert store.jobs == []

    def test_load_existing(self, tmp_path):
        store_file = tmp_path / "cron.json"
        store_file.write_text(json.dumps({
            "version": 1,
            "jobs": [{
                "id": "j1",
                "name": "Test Job",
                "enabled": True,
                "schedule": {"kind": "every", "everyMs": 60000},
                "payload": {"kind": "agent_turn", "message": "Run task"},
                "state": {"nextRunAtMs": None},
                "createdAtMs": 1000,
                "updatedAtMs": 1000,
            }]
        }))
        svc = CronService(store_path=store_file)
        store = svc._load_store()
        assert len(store.jobs) == 1
        assert store.jobs[0].name == "Test Job"

    def test_load_invalid_json(self, tmp_path):
        store_file = tmp_path / "cron.json"
        store_file.write_text("not json{")
        svc = CronService(store_path=store_file)
        store = svc._load_store()
        assert store.jobs == []

    def test_cached_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        store1 = svc._load_store()
        store2 = svc._load_store()
        assert store1 is store2


class TestCronServiceSaveStore:
    def test_save(self, tmp_path):
        store_file = tmp_path / "cron.json"
        svc = CronService(store_path=store_file)
        svc._store = CronStore(jobs=[
            CronJob(
                id="j1", name="Test",
                schedule=CronSchedule(kind="every", every_ms=60000),
                payload=CronPayload(message="hello"),
            )
        ])
        svc._save_store()
        assert store_file.exists()
        data = json.loads(store_file.read_text())
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["name"] == "Test"

    def test_save_no_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._save_store()  # Should not raise


class TestCronServiceAddJob:
    def test_add_every_job(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = svc.add_job(
            name="Every Minute",
            schedule=CronSchedule(kind="every", every_ms=60000),
            message="check status",
        )
        assert job.name == "Every Minute"
        assert job.enabled is True
        assert job.payload.message == "check status"
        assert len(svc.list_jobs()) == 1

    def test_add_at_job(self, tmp_path):
        now = _now_ms()
        svc = CronService(store_path=tmp_path / "cron.json")
        job = svc.add_job(
            name="One Shot",
            schedule=CronSchedule(kind="at", at_ms=now + 60000),
            message="do once",
            delete_after_run=True,
        )
        assert job.delete_after_run is True
        assert job.state.next_run_at_ms == now + 60000


class TestCronServiceRemoveJob:
    def test_remove_existing(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = svc.add_job("temp", CronSchedule(kind="every", every_ms=1000), "msg")
        assert svc.remove_job(job.id) is True
        assert len(svc.list_jobs()) == 0

    def test_remove_nonexistent(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        assert svc.remove_job("fake-id") is False


class TestCronServiceEnableJob:
    def test_disable_job(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = svc.add_job("test", CronSchedule(kind="every", every_ms=1000), "msg")
        result = svc.enable_job(job.id, enabled=False)
        assert result is not None
        assert result.enabled is False
        assert result.state.next_run_at_ms is None

    def test_enable_job(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = svc.add_job("test", CronSchedule(kind="every", every_ms=1000), "msg")
        svc.enable_job(job.id, enabled=False)
        result = svc.enable_job(job.id, enabled=True)
        assert result is not None
        assert result.enabled is True

    def test_enable_nonexistent(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        assert svc.enable_job("fake") is None


class TestCronServiceListJobs:
    def test_list_enabled_only(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        j1 = svc.add_job("active", CronSchedule(kind="every", every_ms=1000), "msg")
        j2 = svc.add_job("inactive", CronSchedule(kind="every", every_ms=2000), "msg")
        svc.enable_job(j2.id, enabled=False)
        jobs = svc.list_jobs(include_disabled=False)
        assert len(jobs) == 1

    def test_list_all(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc.add_job("a", CronSchedule(kind="every", every_ms=1000), "msg")
        svc.add_job("b", CronSchedule(kind="every", every_ms=2000), "msg")
        assert len(svc.list_jobs(include_disabled=True)) == 2


class TestCronServiceRunJob:
    @pytest.mark.asyncio
    async def test_run_enabled_job(self, tmp_path):
        callback = AsyncMock(return_value="done")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        job = svc.add_job("test", CronSchedule(kind="every", every_ms=60000), "msg")
        result = await svc.run_job(job.id)
        assert result is True
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_disabled_job_blocked(self, tmp_path):
        callback = AsyncMock()
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        job = svc.add_job("test", CronSchedule(kind="every", every_ms=60000), "msg")
        svc.enable_job(job.id, enabled=False)
        result = await svc.run_job(job.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_run_disabled_forced(self, tmp_path):
        callback = AsyncMock(return_value="forced")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        job = svc.add_job("test", CronSchedule(kind="every", every_ms=60000), "msg")
        svc.enable_job(job.id, enabled=False)
        result = await svc.run_job(job.id, force=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_run_nonexistent(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        result = await svc.run_job("fake")
        assert result is False


class TestCronServiceStatus:
    @pytest.mark.asyncio
    async def test_status(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._running = True
        svc.add_job("test", CronSchedule(kind="every", every_ms=60000), "msg")
        status = svc.status()
        assert status["enabled"] is True
        assert status["jobs"] == 1


class TestCronServiceExecuteJob:
    @pytest.mark.asyncio
    async def test_execute_success(self, tmp_path):
        callback = AsyncMock(return_value="ok")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        job = CronJob(
            id="j1", name="test",
            schedule=CronSchedule(kind="every", every_ms=60000),
            payload=CronPayload(message="do it"),
        )
        svc._store = CronStore(jobs=[job])
        await svc._execute_job(job)
        assert job.state.last_status == "ok"
        assert job.state.last_error is None

    @pytest.mark.asyncio
    async def test_execute_error(self, tmp_path):
        callback = AsyncMock(side_effect=Exception("boom"))
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        job = CronJob(
            id="j1", name="test",
            schedule=CronSchedule(kind="every", every_ms=60000),
        )
        svc._store = CronStore(jobs=[job])
        await svc._execute_job(job)
        assert job.state.last_status == "error"
        assert "boom" in job.state.last_error

    @pytest.mark.asyncio
    async def test_execute_at_job_disables(self, tmp_path):
        callback = AsyncMock(return_value="ok")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        now = _now_ms()
        job = CronJob(
            id="j1", name="one-shot",
            schedule=CronSchedule(kind="at", at_ms=now + 1000),
        )
        svc._store = CronStore(jobs=[job])
        await svc._execute_job(job)
        assert job.enabled is False

    @pytest.mark.asyncio
    async def test_execute_at_delete_after_run(self, tmp_path):
        callback = AsyncMock(return_value="ok")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        now = _now_ms()
        job = CronJob(
            id="j1", name="one-shot",
            schedule=CronSchedule(kind="at", at_ms=now + 1000),
            delete_after_run=True,
        )
        svc._store = CronStore(jobs=[job])
        await svc._execute_job(job)
        assert len(svc._store.jobs) == 0


class TestCronServiceStartStop:
    @pytest.mark.asyncio
    async def test_start(self, tmp_path):
        store_file = tmp_path / "cron.json"
        svc = CronService(store_path=store_file)
        svc.add_job("test", CronSchedule(kind="every", every_ms=600000), "msg")
        await svc.start()
        assert svc._running is True
        assert svc._store is not None
        svc.stop()

    @pytest.mark.asyncio
    async def test_start_empty(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        await svc.start()
        assert svc._running is True
        svc.stop()

    def test_stop(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._running = True
        svc._timer_task = None
        svc.stop()
        assert svc._running is False

    def test_stop_cancels_timer(self, tmp_path):
        import asyncio
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._running = True
        mock_task = asyncio.Future()
        svc._timer_task = mock_task
        svc.stop()
        assert svc._timer_task is None


class TestCronServiceRecomputeNextRuns:
    def test_recompute_no_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._store = None
        svc._recompute_next_runs()  # Should not raise

    def test_recompute_with_jobs(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = CronJob(
            id="j1", name="test",
            schedule=CronSchedule(kind="every", every_ms=60000),
        )
        svc._store = CronStore(jobs=[job])
        svc._recompute_next_runs()
        assert job.state.next_run_at_ms is not None

    def test_recompute_disabled_job_skipped(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        job = CronJob(
            id="j1", name="test", enabled=False,
            schedule=CronSchedule(kind="every", every_ms=60000),
        )
        svc._store = CronStore(jobs=[job])
        svc._recompute_next_runs()
        assert job.state.next_run_at_ms is None


class TestCronServiceGetNextWake:
    def test_no_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._store = None
        assert svc._get_next_wake_ms() is None

    def test_no_enabled_jobs(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._store = CronStore(jobs=[])
        assert svc._get_next_wake_ms() is None

    def test_returns_earliest(self, tmp_path):
        now = _now_ms()
        svc = CronService(store_path=tmp_path / "cron.json")
        j1 = CronJob(id="j1", name="a", schedule=CronSchedule(kind="every", every_ms=60000))
        j1.state.next_run_at_ms = now + 10000
        j2 = CronJob(id="j2", name="b", schedule=CronSchedule(kind="every", every_ms=30000))
        j2.state.next_run_at_ms = now + 5000
        svc._store = CronStore(jobs=[j1, j2])
        assert svc._get_next_wake_ms() == now + 5000


class TestCronServiceOnTimer:
    @pytest.mark.asyncio
    async def test_on_timer_no_store(self, tmp_path):
        svc = CronService(store_path=tmp_path / "cron.json")
        svc._store = None
        await svc._on_timer()  # Should return early

    @pytest.mark.asyncio
    async def test_on_timer_runs_due_jobs(self, tmp_path):
        callback = AsyncMock(return_value="done")
        svc = CronService(store_path=tmp_path / "cron.json", on_job=callback)
        now = _now_ms()
        job = CronJob(
            id="j1", name="test",
            schedule=CronSchedule(kind="every", every_ms=60000),
            payload=CronPayload(message="test"),
        )
        job.state.next_run_at_ms = now - 1000  # Past due
        svc._store = CronStore(jobs=[job])
        svc._running = False  # Prevent _arm_timer from creating tasks
        await svc._on_timer()
        callback.assert_called_once()


class TestNowMs:
    def test_returns_int(self):
        result = _now_ms()
        assert isinstance(result, int)
        assert result > 0

    def test_approximate_value(self):
        result = _now_ms()
        expected = int(time.time() * 1000)
        assert abs(result - expected) < 100
