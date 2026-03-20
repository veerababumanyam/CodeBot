"""Worktree pool manager using asyncio.Queue.

Provides pre-created git worktrees for fast acquisition by coding agents,
with overflow support when the pool is exhausted during parallel execution.
"""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4

from codebot.worktree.models import WorktreeInfo

logger = logging.getLogger(__name__)


class WorktreePool:
    """Manages a pool of git worktrees for parallel agent isolation.

    Worktrees are pre-created during ``initialize()`` and handed out via
    ``acquire()``.  When the pool is exhausted, overflow worktrees are
    created on demand.  Non-overflow worktrees are returned to the pool
    on ``release()``; overflow worktrees are destroyed.

    Args:
        repo_path: Path to the main git repository.
        pool_dir: Directory where worktree checkouts are stored.
        pool_size: Number of pre-created worktrees in the pool.
    """

    def __init__(
        self,
        repo_path: str,
        pool_dir: str,
        pool_size: int = 5,
    ) -> None:
        self.repo_path = repo_path
        self.pool_dir = pool_dir
        self.pool_size = pool_size
        self.available: asyncio.Queue[WorktreeInfo] = asyncio.Queue()
        self.active: dict[str, WorktreeInfo] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Pre-create worktrees and populate the available queue.

        Prunes stale worktrees from a previous run, creates the pool
        directory, then creates ``pool_size`` fresh worktrees.
        """
        await self._run_git(self.repo_path, "worktree", "prune")
        os.makedirs(self.pool_dir, exist_ok=True)

        for i in range(self.pool_size):
            wt = await self._create_worktree(f"pool-{i}")
            await self.available.put(wt)

        self._initialized = True
        logger.info(
            "Worktree pool initialized with %d worktrees in %s",
            self.pool_size,
            self.pool_dir,
        )

    async def acquire(self, agent_id: str, branch_name: str) -> WorktreeInfo:
        """Acquire a worktree for an agent.

        Tries to get a pre-created worktree from the pool.  If the pool
        is empty, creates an overflow worktree on demand.

        Args:
            agent_id: Identifier of the agent requesting a worktree.
            branch_name: Branch to check out in the worktree.

        Returns:
            A ``WorktreeInfo`` with the agent assignment and branch set.
        """
        try:
            wt = self.available.get_nowait()
        except asyncio.QueueEmpty:
            wt = await self._create_worktree(
                f"overflow-{uuid4().hex[:8]}", is_overflow=True
            )
            logger.info("Created overflow worktree %s for agent %s", wt.id, agent_id)

        await self._run_git(wt.path, "checkout", "-b", branch_name)
        wt.branch = branch_name
        wt.agent_id = agent_id

        async with self._lock:
            self.active[wt.id] = wt

        return wt

    async def release(self, worktree: WorktreeInfo) -> None:
        """Release a worktree back to the pool or destroy if overflow.

        Cleans the worktree state (checkout main, clean, reset) then either
        returns it to the available queue or destroys it if it was an
        overflow worktree.

        Args:
            worktree: The worktree to release.
        """
        async with self._lock:
            self.active.pop(worktree.id, None)

        await self._run_git(worktree.path, "checkout", "main")
        await self._run_git(worktree.path, "clean", "-fd")
        await self._run_git(worktree.path, "reset", "--hard", "HEAD")

        if self.available.qsize() < self.pool_size and not worktree.is_overflow:
            await self.available.put(worktree)
        else:
            await self._destroy_worktree(worktree)

    async def cleanup(self) -> None:
        """Destroy all worktrees (available and active) and prune.

        Drains the available queue, destroys each worktree, then destroys
        all active worktrees under lock, and finally prunes the repo.
        """
        while not self.available.empty():
            try:
                wt = self.available.get_nowait()
                await self._destroy_worktree(wt)
            except asyncio.QueueEmpty:
                break

        async with self._lock:
            for wt in list(self.active.values()):
                await self._destroy_worktree(wt)
            self.active.clear()

        await self._run_git(self.repo_path, "worktree", "prune")
        logger.info("Worktree pool cleaned up")

    async def _create_worktree(
        self, name: str, is_overflow: bool = False
    ) -> WorktreeInfo:
        """Create a new git worktree.

        Args:
            name: Directory name for the worktree within pool_dir.
            is_overflow: Whether this is an overflow worktree.

        Returns:
            A ``WorktreeInfo`` describing the new worktree.
        """
        path = os.path.join(self.pool_dir, name)
        await self._run_git(self.repo_path, "worktree", "add", path, "--detach")
        return WorktreeInfo(id=uuid4().hex, path=path, is_overflow=is_overflow)

    async def _destroy_worktree(self, worktree: WorktreeInfo) -> None:
        """Remove a git worktree.

        Args:
            worktree: The worktree to destroy.
        """
        _, stderr, rc = await self._run_git(
            self.repo_path, "worktree", "remove", worktree.path, "--force"
        )
        if rc != 0:
            logger.warning(
                "Failed to remove worktree %s: %s", worktree.path, stderr
            )

    async def _run_git(
        self, cwd: str, *args: str
    ) -> tuple[str, str, int]:
        """Run a git command asynchronously.

        Uses asyncio.create_subprocess_exec for safe, non-shell execution
        of git commands.  This avoids shell injection and resource leaks
        compared to GitPython.

        Args:
            cwd: Working directory for the command.
            *args: Arguments to pass to git.

        Returns:
            Tuple of (stdout, stderr, return_code).
        """
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            stdout_bytes.decode(),
            stderr_bytes.decode(),
            proc.returncode or 0,
        )

    @property
    def active_count(self) -> int:
        """Number of currently active (acquired) worktrees."""
        return len(self.active)

    @property
    def available_count(self) -> int:
        """Number of worktrees available in the pool."""
        return self.available.qsize()
