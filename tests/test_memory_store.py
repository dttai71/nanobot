"""
Unit tests for MemoryStore (nanobot/agent/memory.py).

Stage: 05 - TEST
Sprint: Sprint 01 - TT-008
"""

import pytest
from pathlib import Path

from nanobot.agent.memory import MemoryStore


@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace with memory directory."""
    return tmp_path


@pytest.fixture
def store(workspace):
    """Create a MemoryStore instance with a temp workspace."""
    return MemoryStore(workspace)


class TestMemoryStore:
    def test_init_creates_memory_dir(self, workspace):
        store = MemoryStore(workspace)
        assert store.memory_dir.exists()
        assert store.memory_dir == workspace / "memory"

    def test_read_long_term_empty(self, store):
        assert store.read_long_term() == ""

    def test_write_and_read_long_term(self, store):
        store.write_long_term("User prefers dark mode")
        assert store.read_long_term() == "User prefers dark mode"

    def test_write_long_term_overwrites(self, store):
        store.write_long_term("first")
        store.write_long_term("second")
        assert store.read_long_term() == "second"

    def test_append_history(self, store):
        store.append_history("[2026-02-16] User asked about weather")
        store.append_history("[2026-02-16] User set a reminder")

        content = store.history_file.read_text(encoding="utf-8")
        assert "[2026-02-16] User asked about weather" in content
        assert "[2026-02-16] User set a reminder" in content

    def test_append_history_strips_trailing_whitespace(self, store):
        store.append_history("entry with trailing spaces   ")
        content = store.history_file.read_text(encoding="utf-8")
        assert content == "entry with trailing spaces\n\n"

    def test_append_history_adds_double_newline(self, store):
        store.append_history("entry1")
        store.append_history("entry2")
        content = store.history_file.read_text(encoding="utf-8")
        assert content == "entry1\n\nentry2\n\n"

    def test_get_memory_context_empty(self, store):
        assert store.get_memory_context() == ""

    def test_get_memory_context_with_content(self, store):
        store.write_long_term("User lives in Hanoi")
        context = store.get_memory_context()
        assert "Long-term Memory" in context
        assert "User lives in Hanoi" in context

    def test_memory_file_paths(self, store):
        assert store.memory_file.name == "MEMORY.md"
        assert store.history_file.name == "HISTORY.md"

    def test_unicode_content(self, store):
        store.write_long_term("Người dùng ở Hà Nội 🇻🇳")
        assert store.read_long_term() == "Người dùng ở Hà Nội 🇻🇳"

    def test_multiline_long_term(self, store):
        content = "# Facts\n- Name: Alice\n- City: Hanoi\n- Language: Vietnamese"
        store.write_long_term(content)
        assert store.read_long_term() == content
