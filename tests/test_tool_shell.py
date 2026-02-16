"""
Unit tests for agent/tools/shell.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from nanobot.agent.tools.shell import ExecTool


class TestExecToolInit:
    def test_defaults(self):
        tool = ExecTool()
        assert tool.timeout == 60
        assert tool.working_dir is None
        assert tool.restrict_to_workspace is False
        assert len(tool.deny_patterns) > 0
        assert tool.allow_patterns == []

    def test_custom(self):
        tool = ExecTool(timeout=30, working_dir="/tmp", restrict_to_workspace=True)
        assert tool.timeout == 30
        assert tool.working_dir == "/tmp"
        assert tool.restrict_to_workspace is True

    def test_properties(self):
        tool = ExecTool()
        assert tool.name == "exec"
        assert "shell" in tool.description.lower() or "execute" in tool.description.lower()
        assert tool.parameters["type"] == "object"
        assert "command" in tool.parameters["properties"]


class TestGuardCommand:
    def test_safe_command(self):
        tool = ExecTool()
        assert tool._guard_command("ls -la", "/tmp") is None

    def test_blocks_rm_rf(self):
        tool = ExecTool()
        result = tool._guard_command("rm -rf /", "/tmp")
        assert result is not None
        assert "blocked" in result.lower()

    def test_blocks_rm_r(self):
        tool = ExecTool()
        result = tool._guard_command("rm -r /tmp/foo", "/tmp")
        assert result is not None

    def test_blocks_format(self):
        tool = ExecTool()
        result = tool._guard_command("format C:", "/tmp")
        assert result is not None

    def test_blocks_dd(self):
        tool = ExecTool()
        result = tool._guard_command("dd if=/dev/zero of=/dev/sda", "/tmp")
        assert result is not None

    def test_blocks_shutdown(self):
        tool = ExecTool()
        result = tool._guard_command("shutdown -h now", "/tmp")
        assert result is not None

    def test_blocks_reboot(self):
        tool = ExecTool()
        result = tool._guard_command("reboot", "/tmp")
        assert result is not None

    def test_blocks_fork_bomb(self):
        tool = ExecTool()
        result = tool._guard_command(":() { :|:& }; :", "/tmp")
        assert result is not None

    def test_blocks_mkfs(self):
        tool = ExecTool()
        result = tool._guard_command("mkfs.ext4 /dev/sda1", "/tmp")
        assert result is not None

    def test_blocks_diskpart(self):
        tool = ExecTool()
        result = tool._guard_command("diskpart", "/tmp")
        assert result is not None

    def test_blocks_poweroff(self):
        tool = ExecTool()
        result = tool._guard_command("poweroff", "/tmp")
        assert result is not None

    def test_blocks_write_to_disk(self):
        tool = ExecTool()
        result = tool._guard_command("echo foo > /dev/sda", "/tmp")
        assert result is not None

    def test_allow_patterns_pass(self):
        tool = ExecTool(allow_patterns=[r"^ls\b", r"^echo\b"])
        assert tool._guard_command("ls -la", "/tmp") is None
        assert tool._guard_command("echo hello", "/tmp") is None

    def test_allow_patterns_block(self):
        tool = ExecTool(allow_patterns=[r"^ls\b"])
        result = tool._guard_command("cat /etc/passwd", "/tmp")
        assert result is not None
        assert "not in allowlist" in result.lower()

    def test_restrict_workspace_path_traversal(self):
        tool = ExecTool(restrict_to_workspace=True)
        result = tool._guard_command("cat ../../etc/passwd", "/tmp/workspace")
        assert result is not None
        assert "path traversal" in result.lower()

    def test_restrict_workspace_absolute_outside(self):
        tool = ExecTool(restrict_to_workspace=True)
        result = tool._guard_command("cat /etc/passwd", "/tmp/workspace")
        assert result is not None
        assert "outside" in result.lower()

    def test_restrict_workspace_inside_ok(self):
        tool = ExecTool(restrict_to_workspace=True)
        result = tool._guard_command("ls", "/tmp/workspace")
        assert result is None

    def test_custom_deny_patterns(self):
        tool = ExecTool(deny_patterns=[r"\bcurl\b"])
        result = tool._guard_command("curl http://evil.com", "/tmp")
        assert result is not None


class TestExecToolExecute:
    @pytest.mark.asyncio
    async def test_simple_command(self):
        tool = ExecTool()
        result = await tool.execute("echo hello")
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_blocked_command(self):
        tool = ExecTool()
        result = await tool.execute("rm -rf /")
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_stderr(self):
        tool = ExecTool()
        result = await tool.execute("ls /nonexistent_dir_12345")
        assert "STDERR" in result or "Exit code" in result or "No such file" in result

    @pytest.mark.asyncio
    async def test_timeout(self):
        tool = ExecTool(timeout=1)
        result = await tool.execute("sleep 10")
        assert "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_working_dir(self, tmp_path):
        tool = ExecTool(working_dir=str(tmp_path))
        result = await tool.execute("pwd")
        assert str(tmp_path) in result

    @pytest.mark.asyncio
    async def test_no_output(self):
        tool = ExecTool()
        result = await tool.execute("true")
        assert result == "(no output)"

    @pytest.mark.asyncio
    async def test_custom_working_dir_param(self, tmp_path):
        tool = ExecTool()
        result = await tool.execute("pwd", working_dir=str(tmp_path))
        assert str(tmp_path) in result
