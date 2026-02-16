"""
Unit tests for agent/tools/filesystem.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path

from nanobot.agent.tools.filesystem import (
    _resolve_path,
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListDirTool,
)


class TestResolvePath:
    def test_simple(self, tmp_path):
        p = _resolve_path(str(tmp_path / "file.txt"))
        assert p == tmp_path / "file.txt"

    def test_with_allowed_dir(self, tmp_path):
        p = _resolve_path(str(tmp_path / "file.txt"), allowed_dir=tmp_path)
        assert p == tmp_path / "file.txt"

    def test_outside_allowed_dir(self, tmp_path):
        with pytest.raises(PermissionError):
            _resolve_path("/etc/passwd", allowed_dir=tmp_path)

    def test_expands_user(self):
        p = _resolve_path("~/test.txt")
        assert "~" not in str(p)


class TestReadFileTool:
    def test_properties(self):
        tool = ReadFileTool()
        assert tool.name == "read_file"
        assert tool.parameters["type"] == "object"
        assert "path" in tool.parameters["properties"]

    @pytest.mark.asyncio
    async def test_read_existing(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        tool = ReadFileTool()
        result = await tool.execute(str(f))
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, tmp_path):
        tool = ReadFileTool()
        result = await tool.execute(str(tmp_path / "nope.txt"))
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_read_directory(self, tmp_path):
        tool = ReadFileTool()
        result = await tool.execute(str(tmp_path))
        assert "not a file" in result.lower()

    @pytest.mark.asyncio
    async def test_read_restricted(self, tmp_path):
        tool = ReadFileTool(allowed_dir=tmp_path)
        result = await tool.execute("/etc/passwd")
        assert "error" in result.lower()


class TestWriteFileTool:
    def test_properties(self):
        tool = WriteFileTool()
        assert tool.name == "write_file"
        assert "path" in tool.parameters["properties"]
        assert "content" in tool.parameters["properties"]

    @pytest.mark.asyncio
    async def test_write_new(self, tmp_path):
        tool = WriteFileTool()
        f = tmp_path / "out.txt"
        result = await tool.execute(str(f), "hello")
        assert "successfully" in result.lower()
        assert f.read_text() == "hello"

    @pytest.mark.asyncio
    async def test_write_creates_parents(self, tmp_path):
        tool = WriteFileTool()
        f = tmp_path / "sub" / "deep" / "out.txt"
        result = await tool.execute(str(f), "nested")
        assert "successfully" in result.lower()
        assert f.read_text() == "nested"

    @pytest.mark.asyncio
    async def test_write_restricted(self, tmp_path):
        tool = WriteFileTool(allowed_dir=tmp_path)
        result = await tool.execute("/tmp/outside.txt", "hack")
        assert "error" in result.lower()


class TestEditFileTool:
    def test_properties(self):
        tool = EditFileTool()
        assert tool.name == "edit_file"
        assert "old_text" in tool.parameters["properties"]
        assert "new_text" in tool.parameters["properties"]

    @pytest.mark.asyncio
    async def test_edit_success(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        tool = EditFileTool()
        result = await tool.execute(str(f), "hello", "goodbye")
        assert "successfully" in result.lower()
        assert f.read_text() == "goodbye world"

    @pytest.mark.asyncio
    async def test_edit_not_found(self, tmp_path):
        tool = EditFileTool()
        result = await tool.execute(str(tmp_path / "nope.txt"), "a", "b")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_edit_text_not_in_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        tool = EditFileTool()
        result = await tool.execute(str(f), "xyz", "abc")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_edit_duplicate_text(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello hello")
        tool = EditFileTool()
        result = await tool.execute(str(f), "hello", "bye")
        assert "appears" in result.lower() and "2" in result

    @pytest.mark.asyncio
    async def test_edit_restricted(self, tmp_path):
        tool = EditFileTool(allowed_dir=tmp_path)
        result = await tool.execute("/etc/passwd", "a", "b")
        assert "error" in result.lower()


class TestListDirTool:
    def test_properties(self):
        tool = ListDirTool()
        assert tool.name == "list_dir"
        assert "path" in tool.parameters["properties"]

    @pytest.mark.asyncio
    async def test_list_with_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "subdir").mkdir()
        tool = ListDirTool()
        result = await tool.execute(str(tmp_path))
        assert "a.txt" in result
        assert "b.txt" in result
        assert "subdir" in result

    @pytest.mark.asyncio
    async def test_list_empty(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        tool = ListDirTool()
        result = await tool.execute(str(empty))
        assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_list_nonexistent(self, tmp_path):
        tool = ListDirTool()
        result = await tool.execute(str(tmp_path / "nope"))
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_list_file_not_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("content")
        tool = ListDirTool()
        result = await tool.execute(str(f))
        assert "not a directory" in result.lower()

    @pytest.mark.asyncio
    async def test_list_restricted(self, tmp_path):
        tool = ListDirTool(allowed_dir=tmp_path)
        result = await tool.execute("/etc")
        assert "error" in result.lower()
