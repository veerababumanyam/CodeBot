"""Context Management System for CodeBot agents.

Provides three-tier context loading (L0/L1/L2), token budget enforcement,
context compression, and the ContextAdapter entry point for assembling
agent context from all tiers.
"""

from codebot.context.adapter import ContextAdapter
from codebot.context.budget import TokenBudget
from codebot.context.compressor import CompressionResult, ContextCompressor
from codebot.context.models import (
    AgentContext,
    CodeSymbol,
    ContextItem,
    L0Context,
    L1Context,
    Priority,
)
from codebot.context.tiers import ThreeTierLoader

__all__ = [
    "AgentContext",
    "CodeSymbol",
    "CompressionResult",
    "ContextAdapter",
    "ContextCompressor",
    "ContextItem",
    "L0Context",
    "L1Context",
    "Priority",
    "ThreeTierLoader",
    "TokenBudget",
]
