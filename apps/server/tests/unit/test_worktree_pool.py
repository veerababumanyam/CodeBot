"""Unit tests for WorktreePool lifecycle management."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from codebot.worktree.models import WorktreeInfo
from codebot.worktree.pool import WorktreePool


@pytest.fixture
def pool(tmp_path: object) -> WorktreePool:
    """Create a WorktreePool with tmp_path for repo and pool dirs."""
    import pathlib

    base = pathlib.Path(str(tmp_path))
    repo = base / "repo"
    repo.mkdir()
    pool_dir = base / "worktrees"
    pool_dir.mkdir()
    return WorktreePool(
        repo_path=str(repo),
        pool_dir=str(pool_dir),
        pool_size=3,
    )


@pytest.fixture
def mock_git() -> AsyncMock:
    """Mock _run_git to return success for all git commands."""
    return AsyncMock(return_value=("", "", 0))


@pytest.mark.asyncio
async def test_initialize_creates_pool(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """After initialize(), available_count should equal pool_size."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()

    assert pool.available_count == 3
    assert pool.active_count == 0
    assert pool._initialized is True


@pytest.mark.asyncio
async def test_acquire_returns_worktree(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """acquire() should return a WorktreeInfo with agent_id and branch set."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()
        wt = await pool.acquire(agent_id="backend-dev", branch_name="feature/test")

    assert isinstance(wt, WorktreeInfo)
    assert wt.agent_id == "backend-dev"
    assert wt.branch == "feature/test"
    assert pool.active_count == 1
    assert pool.available_count == 2


@pytest.mark.asyncio
async def test_acquire_overflow_when_pool_empty(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """When pool is exhausted, acquire() should create an overflow worktree."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()

        # Exhaust the pool (pool_size=3)
        worktrees = []
        for i in range(3):
            wt = await pool.acquire(
                agent_id=f"agent-{i}", branch_name=f"feature/task-{i}"
            )
            worktrees.append(wt)

        assert pool.available_count == 0
        assert pool.active_count == 3

        # Next acquire should create overflow
        overflow_wt = await pool.acquire(
            agent_id="agent-overflow", branch_name="feature/overflow"
        )

    assert overflow_wt.is_overflow is True
    assert pool.active_count == 4


@pytest.mark.asyncio
async def test_release_returns_to_pool(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """release() should return a non-overflow worktree to the available queue."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()
        wt = await pool.acquire(agent_id="backend-dev", branch_name="feature/test")

        assert pool.available_count == 2
        assert pool.active_count == 1

        await pool.release(wt)

    assert pool.available_count == 3
    assert pool.active_count == 0


@pytest.mark.asyncio
async def test_release_destroys_overflow(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """release() should destroy overflow worktrees instead of returning to pool."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()

        # Exhaust pool and create overflow
        worktrees = []
        for i in range(3):
            wt = await pool.acquire(
                agent_id=f"agent-{i}", branch_name=f"feature/task-{i}"
            )
            worktrees.append(wt)

        overflow_wt = await pool.acquire(
            agent_id="agent-overflow", branch_name="feature/overflow"
        )
        assert overflow_wt.is_overflow is True
        assert pool.active_count == 4

        # Release all non-overflow to restore pool
        for wt in worktrees:
            await pool.release(wt)

        # Release overflow -- should NOT increase available_count beyond pool_size
        await pool.release(overflow_wt)

    assert pool.available_count == 3
    assert pool.active_count == 0


@pytest.mark.asyncio
async def test_cleanup_removes_all(
    pool: WorktreePool, mock_git: AsyncMock
) -> None:
    """cleanup() should destroy all worktrees (active and available)."""
    with patch.object(pool, "_run_git", mock_git):
        await pool.initialize()
        await pool.acquire(agent_id="backend-dev", branch_name="feature/test")

        assert pool.active_count == 1
        assert pool.available_count == 2

        await pool.cleanup()

    assert pool.active_count == 0
    assert pool.available_count == 0
