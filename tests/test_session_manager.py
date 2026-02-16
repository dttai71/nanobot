"""
Unit tests for session/manager.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from nanobot.session.manager import Session, SessionManager


class TestSession:
    def test_init(self):
        s = Session(key="telegram:123")
        assert s.key == "telegram:123"
        assert s.messages == []
        assert s.last_consolidated == 0

    def test_add_message(self):
        s = Session(key="test")
        s.add_message("user", "hello")
        assert len(s.messages) == 1
        assert s.messages[0]["role"] == "user"
        assert s.messages[0]["content"] == "hello"
        assert "timestamp" in s.messages[0]

    def test_add_message_kwargs(self):
        s = Session(key="test")
        s.add_message("assistant", "reply", tool_calls=[{"id": "1"}])
        assert s.messages[0]["tool_calls"] == [{"id": "1"}]

    def test_get_history(self):
        s = Session(key="test")
        s.add_message("user", "hi")
        s.add_message("assistant", "hello")
        history = s.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "hi"}
        assert history[1] == {"role": "assistant", "content": "hello"}

    def test_get_history_limit(self):
        s = Session(key="test")
        for i in range(10):
            s.add_message("user", f"msg{i}")
        history = s.get_history(max_messages=3)
        assert len(history) == 3
        assert history[0]["content"] == "msg7"

    def test_clear(self):
        s = Session(key="test")
        s.add_message("user", "hello")
        s.last_consolidated = 5
        s.clear()
        assert s.messages == []
        assert s.last_consolidated == 0


class TestSessionManager:
    @pytest.fixture(autouse=True)
    def _isolate_sessions_dir(self, tmp_path):
        """Override sessions_dir to use tmp_path for isolation."""
        self._sessions_dir = tmp_path / "sessions"
        self._sessions_dir.mkdir()

    def _make_mgr(self, tmp_path):
        mgr = SessionManager(workspace=tmp_path)
        mgr.sessions_dir = self._sessions_dir
        return mgr

    def test_init(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        assert mgr.workspace == tmp_path

    def test_get_or_create_new(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        session = mgr.get_or_create("test:123")
        assert session.key == "test:123"
        assert session.messages == []

    def test_get_or_create_cached(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        s1 = mgr.get_or_create("test:123")
        s2 = mgr.get_or_create("test:123")
        assert s1 is s2

    def test_save_and_load(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        session = mgr.get_or_create("chan:456")
        session.add_message("user", "hello")
        session.add_message("assistant", "hi there")
        mgr.save(session)

        # Clear cache and reload
        mgr.invalidate("chan:456")
        loaded = mgr.get_or_create("chan:456")
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["role"] == "user"
        assert loaded.messages[1]["content"] == "hi there"

    def test_invalidate(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        s = mgr.get_or_create("test:1")
        mgr.invalidate("test:1")
        assert "test:1" not in mgr._cache

    def test_list_sessions(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        s1 = mgr.get_or_create("chan:1")
        s1.add_message("user", "a")
        mgr.save(s1)

        s2 = mgr.get_or_create("chan:2")
        s2.add_message("user", "b")
        mgr.save(s2)

        sessions = mgr.list_sessions()
        assert len(sessions) == 2

    def test_get_session_path(self, tmp_path):
        mgr = self._make_mgr(tmp_path)
        path = mgr._get_session_path("telegram:12345")
        assert path.suffix == ".jsonl"
        assert "telegram" in str(path)
