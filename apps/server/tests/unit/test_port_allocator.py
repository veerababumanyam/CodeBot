"""Unit tests for PortAllocator race-free port reservation."""

from __future__ import annotations

import pytest

from codebot.worktree.port_allocator import PortAllocator


@pytest.mark.asyncio
async def test_allocate_returns_ports_for_services() -> None:
    """allocate() should return a port (int > 0) for each requested service."""
    allocator = PortAllocator()
    ports = await allocator.allocate("wt-001", ["web", "api", "db"])

    assert len(ports) == 3
    for service in ("web", "api", "db"):
        assert service in ports
        assert isinstance(ports[service], int)
        assert ports[service] > 0


@pytest.mark.asyncio
async def test_allocate_different_worktrees_different_ports() -> None:
    """Different worktree IDs should get different ports for the same service."""
    allocator = PortAllocator()
    ports1 = await allocator.allocate("wt-001", ["web"])
    ports2 = await allocator.allocate("wt-002", ["web"])

    assert ports1["web"] != ports2["web"]


@pytest.mark.asyncio
async def test_release_removes_allocation() -> None:
    """release() should remove all port allocations for the given worktree ID."""
    allocator = PortAllocator()
    await allocator.allocate("wt-001", ["web", "api"])

    assert "wt-001" in allocator.allocated

    await allocator.release("wt-001")

    assert "wt-001" not in allocator.allocated


@pytest.mark.asyncio
async def test_allocate_empty_services() -> None:
    """Allocating with an empty services list should return an empty dict."""
    allocator = PortAllocator()
    ports = await allocator.allocate("wt-001", [])

    assert ports == {}
