"""Tests for GateManager and GateDecision human approval gate logic.

Validates the decision logic for human-in-the-loop approval gates:
- should_gate determines if a phase pauses for approval
- build_gate_id creates deterministic gate IDs
- resolve_timeout determines timeout behavior
- GateDecision captures gate decisions with metadata
"""

from __future__ import annotations

import dataclasses

from codebot.pipeline.gates import GateDecision, GateManager
from codebot.pipeline.models import GateConfig


class TestShouldGate:
    """Tests for GateManager.should_gate."""

    def test_returns_true_when_enabled(self) -> None:
        """should_gate returns True when gate.enabled is True."""
        config = GateConfig(enabled=True)
        assert GateManager.should_gate(config) is True

    def test_returns_false_when_disabled(self) -> None:
        """should_gate returns False when gate.enabled is False."""
        config = GateConfig(enabled=False)
        assert GateManager.should_gate(config) is False

    def test_returns_true_for_mandatory_gate(self) -> None:
        """should_gate returns True for mandatory gates regardless of enabled flag."""
        config = GateConfig(enabled=False, mandatory=True)
        assert GateManager.should_gate(config) is True

    def test_returns_true_for_mandatory_and_enabled(self) -> None:
        """should_gate returns True when both mandatory and enabled."""
        config = GateConfig(enabled=True, mandatory=True)
        assert GateManager.should_gate(config) is True


class TestBuildGateId:
    """Tests for GateManager.build_gate_id."""

    def test_creates_deterministic_id(self) -> None:
        """build_gate_id creates deterministic ID from phase name."""
        gate_id = GateManager.build_gate_id("design")
        assert gate_id == "gate_design"

    def test_different_phases_different_ids(self) -> None:
        """Different phase names produce different gate IDs."""
        assert GateManager.build_gate_id("design") != GateManager.build_gate_id("implement")

    def test_id_format(self) -> None:
        """Gate ID follows 'gate_{phase_name}' format."""
        gate_id = GateManager.build_gate_id("testing_phase")
        assert gate_id == "gate_testing_phase"


class TestResolveTimeout:
    """Tests for GateManager.resolve_timeout."""

    def test_returns_auto_approve(self) -> None:
        """resolve_timeout returns 'auto_approve' when timeout_action is 'auto_approve'."""
        config = GateConfig(enabled=True, timeout_action="auto_approve")
        assert GateManager.resolve_timeout(config) == "auto_approve"

    def test_returns_pause(self) -> None:
        """resolve_timeout returns 'pause' when timeout_action is 'pause'."""
        config = GateConfig(enabled=True, timeout_action="pause")
        assert GateManager.resolve_timeout(config) == "pause"


class TestGateDecision:
    """Tests for GateDecision dataclass."""

    def test_fields(self) -> None:
        """GateDecision has gate_id, decision, feedback, and decided_at fields."""
        gd = GateDecision(
            gate_id="gate_design",
            decision="approved",
            feedback="Looks good",
        )
        assert gd.gate_id == "gate_design"
        assert gd.decision == "approved"
        assert gd.feedback == "Looks good"
        assert gd.decided_at  # should have a non-empty default

    def test_default_feedback_is_empty(self) -> None:
        """GateDecision defaults feedback to empty string."""
        gd = GateDecision(gate_id="gate_test", decision="rejected")
        assert gd.feedback == ""

    def test_decided_at_auto_populated(self) -> None:
        """GateDecision auto-populates decided_at with ISO timestamp."""
        gd = GateDecision(gate_id="gate_test", decision="auto_approved")
        # Should be an ISO format string containing 'T' and timezone info
        assert "T" in gd.decided_at

    def test_is_dataclass(self) -> None:
        """GateDecision is a dataclass."""
        assert dataclasses.is_dataclass(GateDecision)
