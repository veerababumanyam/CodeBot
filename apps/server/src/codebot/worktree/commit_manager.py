"""Structured commit manager with agent attribution.

Creates git commits in agent worktrees with conventional messages and
trailers identifying the agent and task that produced the code.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


class CommitManager:
    """Creates structured git commits within an agent worktree.

    Each commit includes the agent ID as a trailer and optionally
    a task reference, providing full traceability from code back to
    the pipeline task that generated it.

    Args:
        worktree_path: Absolute path to the agent's worktree directory.
    """

    def __init__(self, worktree_path: str) -> None:
        self.worktree_path = worktree_path

    async def commit(
        self,
        message: str,
        paths: list[str],
        agent_id: str,
        task_id: str = "",
    ) -> str:
        """Stage files and create a commit with agent attribution.

        Args:
            message: Commit message (first line).
            paths: List of file paths to stage.
            agent_id: Identifier of the agent creating the commit.
            task_id: Optional task reference to include in the trailer.

        Returns:
            The full commit SHA hash.
        """
        for path in paths:
            await self._run_git("add", path)

        full_message = f"{message}\n\nAgent: {agent_id}"
        if task_id:
            full_message += f"\nRefs: {task_id}"

        await self._run_git("commit", "-m", full_message)

        stdout, _, _ = await self._run_git("rev-parse", "HEAD")
        return stdout.strip()

    async def get_diff(self) -> str:
        """Get the staged diff.

        Returns:
            The output of ``git diff --cached``.
        """
        stdout, _, _ = await self._run_git("diff", "--cached")
        return stdout

    async def _run_git(self, *args: str) -> tuple[str, str, int]:
        """Run a git command in the worktree directory via subprocess.

        Args:
            *args: Arguments to pass to git.

        Returns:
            Tuple of (stdout, stderr, return_code).
        """
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=self.worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            stdout_bytes.decode(),
            stderr_bytes.decode(),
            proc.returncode or 0,
        )
