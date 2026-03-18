"""Context management data models.

Defines the core types used throughout the context management system:
- Priority enum for item importance ranking
- ContextItem for individual pieces of context
- AgentContext for managing a collection of context items with budget
- L0Context / L1Context for tier-specific data
- CodeSymbol for tree-sitter extracted symbols
"""

from __future__ import annotations

import enum
import uuid

from pydantic import BaseModel

from codebot.context.budget import TokenBudget


class Priority(str, enum.Enum):
    """Priority levels for context items.

    Higher-priority items are retained when budget is exceeded.
    CRITICAL items are never dropped.
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ContextItem(BaseModel):
    """A single piece of context with metadata.

    Attributes:
        id: Unique identifier for this item.
        content: The text content.
        priority: Importance level for budget decisions.
        token_count: Number of tokens in the content.
        source: Origin tier (``l0``, ``l1``, ``l2``, ``memory``, ``task``).
    """

    id: str
    content: str
    priority: Priority
    token_count: int
    source: str


class CodeSymbol(BaseModel):
    """A code symbol extracted by tree-sitter.

    Attributes:
        name: Symbol name (function, class, etc.).
        kind: Symbol kind -- ``function``, ``class``, ``method``, or ``import``.
        file_path: Path to the source file.
        line_start: Starting line number (1-based).
        line_end: Ending line number (1-based).
        signature: The symbol's signature or declaration text.
        docstring: Optional docstring if present.
    """

    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: str | None = None


class L0Context(BaseModel):
    """Tier-0 context: always present for every agent call.

    Contains project-level essentials that never change during a pipeline run.
    Capped at ~2K tokens.

    Attributes:
        project_name: Name of the project.
        project_description: Brief description of the project.
        tech_stack: List of technologies used.
        conventions: Coding conventions as raw text.
        pipeline_phase: Current pipeline phase name.
        agent_system_prompt: System prompt for the agent.
        constraints: Non-functional requirements and constraints.
    """

    project_name: str
    project_description: str
    tech_stack: list[str]
    conventions: str
    pipeline_phase: str
    agent_system_prompt: str
    constraints: list[str] = []


class L1Context(BaseModel):
    """Tier-1 context: phase-scoped materials loaded on demand.

    Contains files and decisions relevant to the current phase and agent role.

    Attributes:
        phase_requirements: Requirements for the current phase.
        related_files: List of file paths loaded as context.
        architecture_decisions: Architecture decision records.
        upstream_outputs: Outputs from upstream pipeline phases.
    """

    phase_requirements: str
    related_files: list[str]
    architecture_decisions: str = ""
    upstream_outputs: dict[str, object] = {}


class AgentContext:
    """Mutable context container with token budget enforcement.

    Unlike the Pydantic models above, AgentContext is a regular class to
    support in-place mutation (adding/removing items, tracking budget).

    Example::

        ctx = AgentContext(budget=4000, model="gpt-4o")
        ctx.add("project config...", Priority.CRITICAL, source="l0")
        ctx.add("relevant code...", Priority.MEDIUM, source="l1")
        if ctx.is_over_budget():
            ctx.remove_items_by_priority(Priority.LOW)
        prompt = ctx.to_text()
    """

    __slots__ = ("_budget", "_items")

    def __init__(self, budget: int, model: str = "gpt-4o") -> None:
        """Initialize an agent context with a token budget.

        Args:
            budget: Maximum number of tokens allowed.
            model: Model name for tokenizer selection.
        """
        self._budget = TokenBudget(max_tokens=budget, model=model)
        self._items: list[ContextItem] = []

    def add(self, content: str, priority: Priority, source: str = "") -> bool:
        """Add a content item to the context.

        Counts tokens, creates a ContextItem, appends it, and returns
        whether the context is still within budget.

        Args:
            content: Text content to add.
            priority: Importance level.
            source: Origin tier identifier.

        Returns:
            True if the context is still within budget after adding.
        """
        token_count = self._budget.consume(content)
        item = ContextItem(
            id=f"{source}_{uuid.uuid4().hex[:8]}",
            content=content,
            priority=priority,
            token_count=token_count,
            source=source,
        )
        self._items.append(item)
        return not self.is_over_budget()

    def has_budget(self, reserve: int = 0) -> bool:
        """Check whether the budget can accommodate additional tokens.

        Args:
            reserve: Number of additional tokens to check for.

        Returns:
            True if there is room for *reserve* more tokens.
        """
        return self._budget.has_budget(needed=reserve)

    def is_over_budget(self) -> bool:
        """Check whether the context has exceeded its token budget.

        Returns:
            True if used tokens exceed the budget.
        """
        return self._budget.used_tokens > self._budget.max_tokens

    def remove_items_by_priority(self, priority: Priority) -> int:
        """Remove all items with the given priority and reclaim tokens.

        Args:
            priority: The priority level to remove.

        Returns:
            Number of tokens reclaimed.
        """
        kept: list[ContextItem] = []
        reclaimed = 0
        for item in self._items:
            if item.priority == priority:
                reclaimed += item.token_count
            else:
                kept.append(item)
        self._items = kept
        self._budget.release(reclaimed)
        return reclaimed

    def to_text(self) -> str:
        """Render all context items as a single string for LLM input.

        Items are joined with ``---`` separators.

        Returns:
            Combined text of all context items.
        """
        return "\n---\n".join(item.content for item in self._items)

    @property
    def total_tokens(self) -> int:
        """Total number of tokens consumed."""
        return self._budget.used_tokens

    @property
    def remaining_budget(self) -> int:
        """Remaining token budget (never negative)."""
        return self._budget.remaining

    @property
    def items(self) -> list[ContextItem]:
        """Current list of context items (read-only copy)."""
        return list(self._items)
