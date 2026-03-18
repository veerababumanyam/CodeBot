"""Protocol stubs for LLM, worktree, and tool dependencies.

These define the interfaces that Phase 4 (Multi-LLM Abstraction) and
Phase 8 (Worktree Isolation) will implement. Phase 3 agents program
against these protocols, enabling clean dependency inversion and
testability via mocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True, kw_only=True)
class LLMResponse:
    """Response from an LLM provider call."""

    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM provider abstraction.

    Phase 4 implements concrete providers (Anthropic, OpenAI, Google, etc.).
    """

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "",
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...


@runtime_checkable
class WorktreeProvider(Protocol):
    """Protocol for git worktree isolation.

    Phase 8 implements full worktree management.
    """

    async def create_worktree(self, agent_id: str, branch_name: str) -> str: ...

    async def cleanup_worktree(self, worktree_path: str) -> None: ...


@runtime_checkable
class ToolRegistry(Protocol):
    """Protocol for agent tool binding and schema retrieval."""

    async def bind(self, agent_id: str, tool_names: list[str]) -> None: ...

    async def get_tool_schemas(self, agent_id: str) -> list[dict[str, Any]]: ...
