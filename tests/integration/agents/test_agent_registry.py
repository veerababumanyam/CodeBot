"""Integration test: verify all 30 AgentType values have registered agent classes.

Tests AGNT-08: System supports 30 specialized agents, all extending BaseAgent,
each with a unique registration in the agent registry.
"""

from __future__ import annotations

import codebot.agents  # noqa: F401 -- triggers all registrations

from agent_sdk.agents.base import BaseAgent
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import get_all_registered


class TestAgentRegistryComplete:
    """Integration tests for complete agent registry."""

    def test_all_30_agents_registered(self) -> None:
        """AGNT-08: System supports 30 specialized agents."""
        registered = get_all_registered()
        all_types = set(AgentType)
        registered_types = set(registered.keys())
        missing = all_types - registered_types
        assert len(registered) == 30, (
            f"Expected 30 registered agents, got {len(registered)}. Missing: {missing}"
        )

    def test_each_agent_type_has_class(self) -> None:
        """Every AgentType enum value maps to a concrete class."""
        registered = get_all_registered()
        for agent_type in AgentType:
            assert agent_type in registered, (
                f"AgentType.{agent_type.name} has no registered class"
            )

    def test_all_classes_are_unique(self) -> None:
        """No two AgentType values map to the same class."""
        registered = get_all_registered()
        classes = list(registered.values())
        assert len(set(id(c) for c in classes)) == len(classes), (
            "Duplicate class registrations found"
        )

    def test_all_agents_extend_base_agent(self) -> None:
        """Every registered agent class extends BaseAgent."""
        registered = get_all_registered()
        for agent_type, cls in registered.items():
            assert issubclass(cls, BaseAgent), (
                f"{cls.__name__} for {agent_type} does not extend BaseAgent"
            )

    def test_all_agents_instantiable(self) -> None:
        """Every registered agent can be instantiated with no arguments."""
        registered = get_all_registered()
        for agent_type, cls in registered.items():
            instance = cls()
            assert instance.agent_type == agent_type, (
                f"{cls.__name__} reports agent_type={instance.agent_type}, "
                f"expected {agent_type}"
            )
