"""Dynamic port allocator for parallel agent worktrees.

Uses ``ephemeral-port-reserve`` for race-free port allocation, ensuring
that parallel agents never contend on the same port numbers.
"""

from __future__ import annotations

import asyncio
import logging

from ephemeral_port_reserve import reserve

logger = logging.getLogger(__name__)


class PortAllocator:
    """Allocates unique ports for services running in agent worktrees.

    Each worktree may need ports for web servers, API servers, databases,
    etc.  This allocator reserves real ports from the OS to prevent
    conflicts during parallel execution.

    The ``reserve()`` function from ``ephemeral-port-reserve`` uses a
    TIME_WAIT trick to ensure the port stays available long enough for
    the subprocess to bind it.
    """

    def __init__(self) -> None:
        self._allocated: dict[str, dict[str, int]] = {}
        self._lock = asyncio.Lock()

    async def allocate(
        self, worktree_id: str, services: list[str]
    ) -> dict[str, int]:
        """Reserve unique ports for each service in a worktree.

        Args:
            worktree_id: Identifier of the worktree requesting ports.
            services: List of service names to allocate ports for.

        Returns:
            Mapping of service name to allocated port number.
        """
        ports: dict[str, int] = {}
        async with self._lock:
            for service in services:
                port = reserve()
                ports[service] = port
            self._allocated[worktree_id] = ports
        logger.debug("Allocated ports for worktree %s: %s", worktree_id, ports)
        return ports

    async def release(self, worktree_id: str) -> None:
        """Release port reservations for a worktree.

        Ports return to the OS pool after TIME_WAIT expires (~60s on Linux).

        Args:
            worktree_id: Identifier of the worktree whose ports to release.
        """
        async with self._lock:
            self._allocated.pop(worktree_id, None)
        logger.debug("Released ports for worktree %s", worktree_id)

    @property
    def allocated(self) -> dict[str, dict[str, int]]:
        """Return a copy of current port allocations."""
        return dict(self._allocated)
