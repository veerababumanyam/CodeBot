"""Unit tests for CLI agent adapters, session manager, output parser, and models."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.cli_agents.adapters.claude_code import ClaudeCodeAdapter
from codebot.cli_agents.adapters.codex import CodexAdapter
from codebot.cli_agents.adapters.gemini import GeminiCLIAdapter
from codebot.cli_agents.health import HealthChecker
from codebot.cli_agents.models import AdapterInfo, CLIResult, CLITask
from codebot.cli_agents.output_parser import OutputParser
from codebot.cli_agents.session import SessionManager


# ── ClaudeCodeAdapter ──────────────────────────────────────────────────


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter.build_command()."""

    def test_claude_code_build_command(self) -> None:
        adapter = ClaudeCodeAdapter()
        task = CLITask(
            prompt="build auth",
            allowed_tools=["read_file", "write_file"],
            max_tokens=8192,
        )
        cmd = adapter.build_command(task, "/tmp/wt1")
        assert cmd[0] == "claude"
        assert "--print" in cmd
        assert "--output-format" in cmd
        assert "json" in cmd
        assert "--allowedTools" in cmd
        assert "read_file,write_file" in cmd

    def test_claude_code_build_command_with_files(self) -> None:
        adapter = ClaudeCodeAdapter()
        task = CLITask(
            prompt="build auth",
            files_context=["src/main.py"],
        )
        cmd = adapter.build_command(task, "/tmp/wt1")
        assert "--file" in cmd
        assert "src/main.py" in cmd


# ── CodexAdapter ───────────────────────────────────────────────────────


class TestCodexAdapter:
    """Tests for CodexAdapter.build_command()."""

    def test_codex_build_command(self) -> None:
        adapter = CodexAdapter()
        task = CLITask(prompt="build auth")
        cmd = adapter.build_command(task, "/tmp/wt1")
        assert cmd[0] == "codex"
        assert "--quiet" in cmd
        assert "--json" in cmd
        assert "--cwd" in cmd


# ── GeminiCLIAdapter ──────────────────────────────────────────────────


class TestGeminiCLIAdapter:
    """Tests for GeminiCLIAdapter.build_command()."""

    def test_gemini_build_command(self) -> None:
        adapter = GeminiCLIAdapter()
        task = CLITask(prompt="build auth")
        cmd = adapter.build_command(task, "/tmp/wt1")
        assert cmd[0] == "gemini"
        assert "--json" in cmd
        assert "--cwd" in cmd


# ── BaseCLIAdapter.build_env / check_available ─────────────────────────


class TestBaseCLIAdapterEnvAndAvailability:
    """Tests for build_env and check_available on adapter instances."""

    def test_build_env_sets_worktree_and_ports(self) -> None:
        adapter = ClaudeCodeAdapter()
        env = adapter.build_env("/tmp/wt1", {"web": 3001, "api": 8001})
        assert env["CODEBOT_WORKTREE"] == "/tmp/wt1"
        assert env["PORT_WEB"] == "3001"
        assert env["PORT_API"] == "8001"

    @pytest.mark.asyncio
    async def test_check_available_true(self) -> None:
        adapter = ClaudeCodeAdapter()
        with patch("shutil.which", return_value="/usr/bin/claude"):
            result = await adapter.check_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_available_false(self) -> None:
        adapter = ClaudeCodeAdapter()
        with patch("shutil.which", return_value=None):
            result = await adapter.check_available()
        assert result is False


# ── OutputParser ───────────────────────────────────────────────────────


class TestOutputParser:
    """Tests for OutputParser JSON extraction."""

    def test_output_parser_parse_json(self) -> None:
        parser = OutputParser()
        result = parser.parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_output_parser_parse_json_embedded(self) -> None:
        parser = OutputParser()
        raw = 'Some CLI output\n{"key": "value"}\nMore output'
        result = parser.parse_json(raw)
        assert result == {"key": "value"}


# ── SessionManager ────────────────────────────────────────────────────


class TestSessionManager:
    """Tests for SessionManager.run()."""

    @pytest.mark.asyncio
    async def test_session_manager_run(self) -> None:
        session = SessionManager()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"output", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await session.run(
                cmd=["echo", "hello"],
                env={"PATH": "/usr/bin"},
                cwd="/tmp",
                timeout=30,
            )

        assert result.stdout == "output"
        assert result.returncode == 0
        assert result.duration_ms >= 0


# ── HealthChecker ─────────────────────────────────────────────────────


class TestHealthChecker:
    """Tests for HealthChecker.check_process and check_binary."""

    @pytest.mark.asyncio
    async def test_health_checker_process_alive(self) -> None:
        checker = HealthChecker()
        proc = MagicMock()
        proc.returncode = None  # Still running
        result = await checker.check_process(proc)
        assert result is True

    @pytest.mark.asyncio
    async def test_health_checker_process_dead(self) -> None:
        checker = HealthChecker()
        proc = MagicMock()
        proc.returncode = 0  # Exited
        result = await checker.check_process(proc)
        assert result is False


# ── Models ────────────────────────────────────────────────────────────


class TestModels:
    """Tests for CLITask and CLIResult Pydantic models."""

    def test_cli_task_model(self) -> None:
        task = CLITask(prompt="build auth")
        assert task.prompt == "build auth"
        assert task.allowed_tools == []
        assert task.max_tokens == 4096
        assert task.files_context == []

    def test_cli_result_security_report_default_none(self) -> None:
        result = CLIResult()
        assert result.security_report is None
