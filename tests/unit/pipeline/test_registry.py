"""Tests for PhaseRegistry mapping phase names to agent lists."""

from __future__ import annotations

import pytest

from codebot.pipeline.registry import PhaseRegistry


class TestPhaseRegistry:
    """Tests for PhaseRegistry."""

    def test_register_and_get_agents(self) -> None:
        registry = PhaseRegistry()
        registry.register("design", ["architect", "designer"])
        assert registry.get_agents("design") == ["architect", "designer"]

    def test_get_agents_unknown_phase_raises(self) -> None:
        registry = PhaseRegistry()
        with pytest.raises(KeyError, match="No agents registered for phase"):
            registry.get_agents("nonexistent")

    def test_register_from_config(self) -> None:
        """PhaseRegistry can be populated from PhaseConfig objects."""
        from codebot.pipeline.models import PhaseConfig

        phases = [
            PhaseConfig(name="init", agents=["orchestrator"]),
            PhaseConfig(name="implement", agents=["backend_dev", "frontend_dev"]),
        ]
        registry = PhaseRegistry()
        registry.register_from_config(phases)
        assert registry.get_agents("init") == ["orchestrator"]
        assert registry.get_agents("implement") == ["backend_dev", "frontend_dev"]

    def test_phase_names(self) -> None:
        registry = PhaseRegistry()
        registry.register("init", ["orchestrator"])
        registry.register("design", ["architect"])
        assert registry.phase_names == ["init", "design"]

    def test_overwrite_registration(self) -> None:
        registry = PhaseRegistry()
        registry.register("init", ["orchestrator"])
        registry.register("init", ["orchestrator", "planner"])
        assert registry.get_agents("init") == ["orchestrator", "planner"]
