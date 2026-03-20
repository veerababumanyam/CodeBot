"""Worktree management subsystem for parallel agent isolation.

Provides git worktree pooling, dynamic port allocation, branch strategy,
and structured commit management for coding agents.
"""

from codebot.worktree.models import (
    BranchConfig,
    MergeResult,
    MergeStrategy,
    WorktreeInfo,
)
from codebot.worktree.port_allocator import PortAllocator
from codebot.worktree.pool import WorktreePool

__all__ = [
    "BranchConfig",
    "MergeResult",
    "MergeStrategy",
    "PortAllocator",
    "WorktreeInfo",
    "WorktreePool",
]
