"""Tool service for managing the tool registry.

Provides create and lookup operations for ToolDefinition objects.
"""

from __future__ import annotations

from codebot.tools.registry import ToolDefinition


class ToolService:
    """Service layer for tool lifecycle management.

    In production, this wraps a database repository. Currently provides
    an in-memory implementation for agent integration.
    """

    def __init__(self) -> None:
        """Initialize with empty in-memory store."""
        self._tools: dict[str, ToolDefinition] = {}

    async def create_tool(self, definition: ToolDefinition) -> None:
        """Register a new tool in the registry.

        Args:
            definition: The ToolDefinition to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if definition.name in self._tools:
            msg = f"Tool with name '{definition.name}' already exists"
            raise ValueError(msg)
        self._tools[definition.name] = definition
