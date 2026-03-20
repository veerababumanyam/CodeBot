"""Unit tests for the AgentRegistry (register, create, list)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import _REGISTRY, create_agent, get_all_registered, register_agent


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure the registry is clean before and after each test."""
    saved = dict(_REGISTRY)
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()
    _REGISTRY.update(saved)


class TestRegisterAgent:
    """register_agent decorator adds class to _REGISTRY."""

    def test_register_agent_adds_to_registry(self) -> None:
        """Registering a class with @register_agent makes it discoverable."""

        @register_agent(AgentType.ORCHESTRATOR)
        @dataclass
        class DummyOrchestrator:
            name: str = "dummy"

        registered = get_all_registered()
        assert AgentType.ORCHESTRATOR in registered
        assert registered[AgentType.ORCHESTRATOR] is DummyOrchestrator


class TestCreateAgent:
    """create_agent factory instantiates registered classes."""

    def test_create_agent_instantiates(self) -> None:
        """create_agent returns an instance of the registered class."""

        @register_agent(AgentType.ORCHESTRATOR)
        @dataclass
        class DummyOrchestrator:
            name: str = "dummy"

        agent = create_agent(AgentType.ORCHESTRATOR)
        assert isinstance(agent, DummyOrchestrator)
        assert agent.name == "dummy"

    def test_create_agent_raises_for_unknown(self) -> None:
        """create_agent raises ValueError for unregistered agent types."""
        with pytest.raises(ValueError, match="No agent registered"):
            create_agent(AgentType.PLANNER)


class TestGetAllRegistered:
    """get_all_registered returns a copy of the registry."""

    def test_get_all_registered_returns_copy(self) -> None:
        """Modifying the returned dict does not affect the internal registry."""

        @register_agent(AgentType.ORCHESTRATOR)
        @dataclass
        class DummyOrchestrator:
            name: str = "dummy"

        copy = get_all_registered()
        copy.pop(AgentType.ORCHESTRATOR)
        # Internal registry should still have it
        assert AgentType.ORCHESTRATOR in get_all_registered()
