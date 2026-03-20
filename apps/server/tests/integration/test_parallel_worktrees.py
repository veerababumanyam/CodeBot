"""Integration tests for parallel worktree execution and security wiring.

Tests verify that CLIAgentRunner correctly acquires worktrees, allocates
ports, runs adapters, and integrates with SecurityOrchestrator.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.cli_agents.models import CLIResult, CLITask
from codebot.cli_agents.runner import CLIAgentRunner
from codebot.security.models import (
    GateResult,
    ScanSummary,
    SecurityReport,
)
from codebot.worktree.branch_strategy import BranchStrategy
from codebot.worktree.models import WorktreeInfo
from codebot.worktree.port_allocator import PortAllocator


def _make_mock_pool(pool_size: int = 3) -> MagicMock:
    """Create a mock WorktreePool with acquire/release behavior."""
    pool = MagicMock()
    _counter = {"n": 0}

    async def _acquire(agent_id: str, branch_name: str) -> WorktreeInfo:
        _counter["n"] += 1
        return WorktreeInfo(
            id=f"wt-{_counter['n']}",
            path=f"/tmp/worktrees/wt-{_counter['n']}",
            branch=branch_name,
            agent_id=agent_id,
        )

    pool.acquire = AsyncMock(side_effect=_acquire)
    pool.release = AsyncMock()
    return pool


def _make_mock_port_allocator() -> MagicMock:
    """Create a mock PortAllocator with unique ports per call."""
    allocator = MagicMock()
    _base = {"port": 3000}

    async def _allocate(
        worktree_id: str, services: list[str]
    ) -> dict[str, int]:
        ports = {}
        for svc in services:
            _base["port"] += 1
            ports[svc] = _base["port"]
        return ports

    allocator.allocate = AsyncMock(side_effect=_allocate)
    allocator.release = AsyncMock()
    return allocator


@pytest.fixture
def mock_session_result() -> CLIResult:
    """A successful CLIResult from a mock session."""
    return CLIResult(
        stdout='{"status": "ok"}',
        stderr="",
        returncode=0,
        duration_ms=100,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_two_agents_parallel_execution(
    mock_session_result: CLIResult,
) -> None:
    """Two agents acquire unique worktrees and ports concurrently."""
    pool = _make_mock_pool(pool_size=3)
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
    )
    task = CLITask(prompt="build feature")

    with patch.object(
        runner.session, "run", return_value=mock_session_result
    ):
        r1, r2 = await asyncio.gather(
            runner.execute("claude", task, "agent-1", "task-1"),
            runner.execute("claude", task, "agent-2", "task-2"),
        )

    assert r1.returncode == 0
    assert r2.returncode == 0

    # Verify unique worktree paths acquired
    acquire_calls = pool.acquire.call_args_list
    assert len(acquire_calls) == 2
    paths = {call.args[0] for call in acquire_calls}
    assert len(paths) == 2  # Two different agent IDs

    # Verify ports allocated for each worktree
    assert port_alloc.allocate.call_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_failure_releases_worktree() -> None:
    """Worktree is released even when the adapter raises an exception."""
    pool = _make_mock_pool()
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
    )
    task = CLITask(prompt="build feature")

    with patch.object(
        runner.session, "run", side_effect=RuntimeError("adapter crash")
    ):
        result = await runner.execute("claude", task, "agent-crash")

    # Runner catches the error and returns a failure result
    assert result.returncode == -1
    assert "adapter crash" in result.stderr

    # Worktree is still released in finally block
    assert pool.release.call_count == 1
    assert port_alloc.release.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_with_security_orchestrator(
    mock_session_result: CLIResult,
) -> None:
    """SecurityOrchestrator.scan() is called and report attached to CLIResult."""
    pool = _make_mock_pool()
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    mock_report = SecurityReport(
        findings=[],
        errors=[],
        summary=ScanSummary(total_findings=0),
        gate_result=GateResult(passed=True, reason="Clean"),
    )

    mock_security_orch = MagicMock()
    mock_security_orch.scan = AsyncMock(return_value=mock_report)

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
        security_orchestrator=mock_security_orch,
    )
    task = CLITask(prompt="implement auth")

    with patch.object(
        runner.session, "run", return_value=mock_session_result
    ):
        result = await runner.execute("claude", task, "agent-sec", "task-sec")

    # Verify scan was called with the worktree path
    mock_security_orch.scan.assert_called_once()
    scan_path = mock_security_orch.scan.call_args.args[0]
    assert scan_path.startswith("/tmp/worktrees/wt-")

    # Verify report is attached
    assert result.security_report is not None
    assert result.security_report.gate_result is not None
    assert result.security_report.gate_result.passed is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_without_security_orchestrator(
    mock_session_result: CLIResult,
) -> None:
    """When security_orchestrator is None, security_report stays None."""
    pool = _make_mock_pool()
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
        security_orchestrator=None,
    )
    task = CLITask(prompt="implement feature")

    with patch.object(
        runner.session, "run", return_value=mock_session_result
    ):
        result = await runner.execute("claude", task, "agent-nosec")

    assert result.security_report is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_security_scan_failure_nonfatal(
    mock_session_result: CLIResult,
) -> None:
    """Security scan failure is logged but does not crash the runner."""
    pool = _make_mock_pool()
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    mock_security_orch = MagicMock()
    mock_security_orch.scan = AsyncMock(
        side_effect=RuntimeError("scanner exploded")
    )

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
        security_orchestrator=mock_security_orch,
    )
    task = CLITask(prompt="build feature")

    with patch.object(
        runner.session, "run", return_value=mock_session_result
    ):
        result = await runner.execute("claude", task, "agent-scanfail")

    # Result is still returned (non-fatal scan failure)
    assert result.returncode == 0
    assert result.security_report is None

    # Worktree and ports were still cleaned up
    assert pool.release.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_available() -> None:
    """CLIAgentRunner.list_available() returns AdapterInfo for each adapter."""
    pool = _make_mock_pool()
    port_alloc = _make_mock_port_allocator()
    branch_strategy = BranchStrategy()

    runner = CLIAgentRunner(
        pool=pool,
        port_allocator=port_alloc,
        branch_strategy=branch_strategy,
    )

    with patch("shutil.which", return_value=None):
        infos = await runner.list_available()

    assert len(infos) == 3
    names = {info.name for info in infos}
    assert "ClaudeCodeAdapter" in names
    assert "CodexAdapter" in names
    assert "GeminiCLIAdapter" in names
