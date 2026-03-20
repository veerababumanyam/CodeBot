"""Shared fixtures for agent unit tests.

Provides mock LLM, EventBus, ContextManager, and Tools fixtures
that all agent tests can use to avoid real external dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Provide a mock LLM provider.

    Returns an AsyncMock with a ``generate`` coroutine whose return value
    has ``.content``, ``.has_tool_calls``, and ``.structured_output`` attrs.
    """
    llm = AsyncMock()
    response = MagicMock()
    response.content = "mock response"
    response.has_tool_calls = False
    response.structured_output = {}
    llm.generate = AsyncMock(return_value=response)
    return llm


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Provide a mock NATS EventBus.

    Returns an AsyncMock with ``publish`` and ``subscribe`` as async callables.
    """
    bus = AsyncMock()
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    return bus


@pytest.fixture
def mock_context_manager() -> AsyncMock:
    """Provide a mock ContextManager with L0/L1/L2 tier accessors.

    Each tier returns an empty dict. ``shared_state`` is an AsyncMock
    with ``get`` and ``set`` methods for shared state access.
    """
    cm = AsyncMock()
    cm.get_l0 = AsyncMock(return_value={})
    cm.get_l1 = AsyncMock(return_value={})
    cm.get_l2 = AsyncMock(return_value={})
    cm.shared_state = AsyncMock()
    cm.shared_state.get = AsyncMock(return_value=None)
    cm.shared_state.set = AsyncMock()
    return cm


@pytest.fixture
def mock_tools() -> AsyncMock:
    """Provide a mock ToolRegistry.

    Returns an AsyncMock with an ``execute`` coroutine that returns an empty list.
    """
    tools = AsyncMock()
    tools.execute = AsyncMock(return_value=[])
    return tools
