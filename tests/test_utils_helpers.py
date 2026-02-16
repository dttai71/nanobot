"""
Unit tests for utils/helpers.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path

from nanobot.utils.helpers import (
    ensure_dir,
    truncate_string,
    safe_filename,
    parse_session_key,
    timestamp,
    get_data_path,
    get_workspace_path,
)


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        new_dir = tmp_path / "subdir" / "nested"
        result = ensure_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory(self, tmp_path):
        result = ensure_dir(tmp_path)
        assert result == tmp_path


class TestTruncateString:
    def test_short_string(self):
        assert truncate_string("hello", 10) == "hello"

    def test_exact_length(self):
        assert truncate_string("hello", 5) == "hello"

    def test_truncated(self):
        result = truncate_string("hello world", 8)
        assert len(result) == 8
        assert result.endswith("...")

    def test_custom_suffix(self):
        result = truncate_string("hello world", 8, suffix="..")
        assert result.endswith("..")


class TestSafeFilename:
    def test_clean_name(self):
        assert safe_filename("hello_world") == "hello_world"

    def test_unsafe_chars_replaced(self):
        result = safe_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_strips_whitespace(self):
        assert safe_filename("  hello  ") == "hello"


class TestParseSessionKey:
    def test_valid_key(self):
        channel, chat_id = parse_session_key("telegram:12345")
        assert channel == "telegram"
        assert chat_id == "12345"

    def test_key_with_colon_in_chat_id(self):
        channel, chat_id = parse_session_key("slack:C:123")
        assert channel == "slack"
        assert chat_id == "C:123"

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            parse_session_key("no_colon")


class TestTimestamp:
    def test_returns_string(self):
        result = timestamp()
        assert isinstance(result, str)
        assert "T" in result  # ISO format


class TestGetDataPath:
    def test_returns_path(self):
        path = get_data_path()
        assert isinstance(path, Path)
        assert ".nanobot" in str(path)


class TestGetWorkspacePath:
    def test_default(self):
        path = get_workspace_path()
        assert isinstance(path, Path)
        assert "workspace" in str(path)

    def test_custom(self, tmp_path):
        path = get_workspace_path(str(tmp_path))
        assert path == tmp_path
