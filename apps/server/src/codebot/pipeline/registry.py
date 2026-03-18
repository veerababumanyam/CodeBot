"""Phase-to-agent mapping registry for pipeline orchestration.

The :class:`PhaseRegistry` maps pipeline phase names to their assigned agent
lists.  It can be populated manually or bulk-loaded from a list of
:class:`~codebot.pipeline.models.PhaseConfig` objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codebot.pipeline.models import PhaseConfig


class PhaseRegistry:
    """Maps pipeline phase names to their assigned agents.

    Example::

        registry = PhaseRegistry()
        registry.register("design", ["architect", "designer"])
        agents = registry.get_agents("design")  # ["architect", "designer"]
    """

    def __init__(self) -> None:
        self._registry: dict[str, list[str]] = {}

    def register(self, phase_name: str, agents: list[str]) -> None:
        """Register agents for a phase, replacing any previous registration.

        Args:
            phase_name: Name of the pipeline phase.
            agents: List of agent identifiers to assign.
        """
        self._registry[phase_name] = agents

    def get_agents(self, phase_name: str) -> list[str]:
        """Return the agents registered for *phase_name*.

        Args:
            phase_name: Name of the pipeline phase.

        Returns:
            List of agent identifiers.

        Raises:
            KeyError: If *phase_name* has no registered agents.
        """
        if phase_name not in self._registry:
            raise KeyError(f"No agents registered for phase: {phase_name}")
        return self._registry[phase_name]

    def register_from_config(self, phases: list[PhaseConfig]) -> None:
        """Populate registry from a list of PhaseConfig objects.

        Args:
            phases: List of :class:`PhaseConfig` instances to register.
        """
        for phase in phases:
            self._registry[phase.name] = list(phase.agents)

    @property
    def phase_names(self) -> list[str]:
        """Return all registered phase names in insertion order."""
        return list(self._registry.keys())
