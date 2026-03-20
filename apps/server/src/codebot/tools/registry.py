"""Tool registry for managing tool definitions.

Defines the ToolDefinition dataclass used by ToolService and ToolsCreatorAgent.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, kw_only=True)
class ToolDefinition:
    """A tool definition registered in the tool registry.

    Attributes:
        name: Unique tool name.
        description: What the tool does.
        parameters: JSON Schema for tool inputs.
        execute: Async callable that implements the tool.
        version: Semantic version string.
        tags: Searchable tags for discovery.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    execute: Callable[..., Awaitable[Any]] | None = None
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
