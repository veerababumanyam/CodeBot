"""Hook service for managing lifecycle hook registration.

Provides register and lookup operations for Hook objects.
"""

from __future__ import annotations

from codebot.hooks.models import Hook


class HookService:
    """Service layer for hook lifecycle management.

    In production, this wraps a database repository. Currently provides
    an in-memory implementation for agent integration.
    """

    def __init__(self) -> None:
        """Initialize with empty in-memory store."""
        self._hooks: dict[str, Hook] = {}

    async def register(self, hook: Hook) -> None:
        """Register a hook in the registry.

        Args:
            hook: The Hook object to register.

        Raises:
            ValueError: If a hook with the same name already exists.
        """
        for existing in self._hooks.values():
            if existing.name == hook.name:
                msg = f"Hook with name '{hook.name}' already exists"
                raise ValueError(msg)
        self._hooks[hook.id] = hook
