"""Branch naming, merge, and conflict detection strategy.

Provides deterministic branch name generation from agent/task metadata,
sequential merge with automatic conflict detection, and merge-tree-based
conflict checking without modifying the working tree.
"""

from __future__ import annotations

import asyncio
import logging
import re

from codebot.worktree.models import BranchConfig, MergeResult

logger = logging.getLogger(__name__)


class BranchStrategy:
    """Manages branch naming conventions and merge operations.

    Branch names follow the pattern ``prefix/task_id-sanitized_agent_id``
    (or ``prefix/sanitized_agent_id`` if no task_id is provided).

    Merges are performed sequentially with ``--no-ff`` to preserve history.
    Conflict detection uses ``git merge-tree`` to avoid modifying the
    working tree.
    """

    def create_branch_name(self, config: BranchConfig) -> str:
        """Generate a deterministic branch name from configuration.

        The agent_id is sanitized: lowercased, non-alphanumeric characters
        (except hyphens) replaced with hyphens, leading/trailing hyphens
        stripped, consecutive hyphens collapsed.

        Args:
            config: Branch configuration with prefix, task_id, and agent_id.

        Returns:
            A sanitized branch name string.
        """
        sanitized = config.agent_id.lower()
        sanitized = re.sub(r"[^a-z0-9-]", "-", sanitized)
        sanitized = re.sub(r"-+", "-", sanitized)
        sanitized = sanitized.strip("-")

        if config.task_id:
            return f"{config.prefix}/{config.task_id}-{sanitized}"
        return f"{config.prefix}/{sanitized}"

    async def merge_sequential(
        self,
        repo_path: str,
        source_branch: str,
        target_branch: str,
    ) -> MergeResult:
        """Merge source branch into target using --no-ff strategy.

        On conflict, collects the list of conflicted files, aborts the
        merge, and returns a ``MergeResult`` with ``success=False``.

        Args:
            repo_path: Path to the git repository.
            source_branch: Branch to merge from.
            target_branch: Branch to merge into.

        Returns:
            A ``MergeResult`` indicating success or failure with conflicts.
        """
        await self._run_git(repo_path, "checkout", target_branch)
        _, stderr, rc = await self._run_git(
            repo_path, "merge", "--no-ff", source_branch
        )

        if rc == 0:
            return MergeResult(
                success=True,
                merged_branch=source_branch,
                target_branch=target_branch,
            )

        # Merge failed -- collect conflicted files
        stdout, _, _ = await self._run_git(
            repo_path, "diff", "--name-only", "--diff-filter=U"
        )
        conflicts = [f for f in stdout.strip().split("\n") if f]

        # Abort the failed merge
        await self._run_git(repo_path, "merge", "--abort")

        logger.warning(
            "Merge conflict: %s -> %s, files: %s",
            source_branch,
            target_branch,
            conflicts,
        )
        return MergeResult(
            success=False,
            merged_branch=source_branch,
            target_branch=target_branch,
            conflicts=conflicts,
            error="Merge conflicts detected",
        )

    async def check_conflicts(
        self,
        repo_path: str,
        source_branch: str,
        target_branch: str,
    ) -> list[str]:
        """Check for merge conflicts without modifying the working tree.

        Uses ``git merge-base`` and ``git merge-tree`` to detect conflicts
        in a read-only manner.

        Args:
            repo_path: Path to the git repository.
            source_branch: Branch to check from.
            target_branch: Branch to check against.

        Returns:
            List of file paths that would conflict during merge.
        """
        base_stdout, _, _ = await self._run_git(
            repo_path, "merge-base", target_branch, source_branch
        )
        base = base_stdout.strip()

        tree_stdout, _, _ = await self._run_git(
            repo_path, "merge-tree", base, target_branch, source_branch
        )

        conflicts: list[str] = []
        if "changed in both" in tree_stdout:
            # Parse merge-tree output for conflicted file paths
            for line in tree_stdout.split("\n"):
                line = line.strip()
                if line.startswith("our") or line.startswith("their"):
                    # Format: "  our    100644 <hash> <path>"
                    parts = line.split()
                    if len(parts) >= 4:
                        file_path = parts[-1]
                        if file_path not in conflicts:
                            conflicts.append(file_path)

        return conflicts

    async def delete_branch(self, repo_path: str, branch_name: str) -> None:
        """Delete a branch, falling back to force-delete on failure.

        Args:
            repo_path: Path to the git repository.
            branch_name: Name of the branch to delete.
        """
        _, stderr, rc = await self._run_git(repo_path, "branch", "-d", branch_name)
        if rc != 0:
            logger.warning(
                "Soft delete failed for branch %s (%s), force deleting",
                branch_name,
                stderr.strip(),
            )
            await self._run_git(repo_path, "branch", "-D", branch_name)

    async def _run_git(
        self, cwd: str, *args: str
    ) -> tuple[str, str, int]:
        """Run a git command asynchronously via subprocess.

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
