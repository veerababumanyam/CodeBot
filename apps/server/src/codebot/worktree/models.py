"""Pydantic v2 models for worktree management.

Defines data transfer objects for worktree lifecycle, branch configuration,
and merge results used across the worktree subsystem.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class MergeStrategy(StrEnum):
    """Strategy for merging worktree branches back to the target branch."""

    SEQUENTIAL = "sequential"
    SQUASH = "squash"
    OCTOPUS = "octopus"


class WorktreeInfo(BaseModel):
    """Metadata for a single git worktree instance.

    Attributes:
        id: Unique identifier for this worktree slot.
        path: Absolute filesystem path to the worktree directory.
        branch: Currently checked-out branch name.
        agent_id: ID of the agent using this worktree (empty if unassigned).
        is_overflow: True if this worktree was created beyond the pool size.
        ports: Mapping of service name to allocated port number.
        created_at: Timestamp when the worktree was created.
    """

    model_config = ConfigDict(frozen=False)

    id: str
    path: str
    branch: str = ""
    agent_id: str = ""
    is_overflow: bool = False
    ports: dict[str, int] = {}
    created_at: datetime = datetime.now(tz=timezone.utc)


class BranchConfig(BaseModel):
    """Configuration for creating a branch name.

    Attributes:
        base_branch: Branch to base the new branch on (default: main).
        prefix: Branch prefix category (e.g. feature, fix, chore).
        task_id: Task identifier to include in the branch name.
        agent_id: Agent identifier used to generate the branch slug.
    """

    model_config = ConfigDict(frozen=True)

    base_branch: str = "main"
    prefix: str = "feature"
    task_id: str = ""
    agent_id: str = ""


class MergeResult(BaseModel):
    """Result of a branch merge operation.

    Attributes:
        success: Whether the merge completed without conflicts.
        merged_branch: Source branch that was merged.
        target_branch: Target branch merged into.
        conflicts: List of file paths with merge conflicts.
        error: Human-readable error description if merge failed.
    """

    model_config = ConfigDict(frozen=True)

    success: bool
    merged_branch: str = ""
    target_branch: str = ""
    conflicts: list[str] = []
    error: str = ""
