"""Worktree management subsystem for parallel agent isolation.

Provides git worktree pooling, dynamic port allocation, branch strategy,
and structured commit management for coding agents.
"""

from codebot.worktree.branch_strategy import BranchStrategy
from codebot.worktree.commit_manager import CommitManager
from codebot.worktree.models import (
    BranchConfig,
    MergeResult,
    MergeStrategy,
    WorktreeInfo,
)
from codebot.worktree.pool import WorktreePool
from codebot.worktree.port_allocator import PortAllocator

__all__ = [
    "BranchConfig",
    "BranchStrategy",
    "CommitManager",
    "MergeResult",
    "MergeStrategy",
    "PortAllocator",
    "WorktreeInfo",
    "WorktreePool",
]
