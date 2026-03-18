"""Human-in-the-loop approval gate logic.

The :class:`GateManager` encapsulates the decision logic for pipeline gates.
It determines *whether* a gate should pause, *what* the gate ID is, and
*what* happens on timeout.  The actual signal waiting and workflow pausing
lives in the Temporal workflow (``SDLCPipelineWorkflow`` in Plan 04).

Classes:
    GateDecision: Captures a gate decision with metadata.
    GateManager: Static methods for gate decision logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from codebot.pipeline.models import GateConfig


@dataclass(slots=True, kw_only=True)
class GateDecision:
    """Records the outcome of a human approval gate.

    Attributes:
        gate_id: Deterministic identifier for this gate (e.g. ``"gate_design"``).
        decision: Outcome -- ``"approved"``, ``"rejected"``, or ``"auto_approved"``.
        feedback: Optional human feedback accompanying the decision.
        decided_at: ISO 8601 timestamp of when the decision was made.
    """

    gate_id: str
    decision: str  # "approved" | "rejected" | "auto_approved"
    feedback: str = ""
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class GateManager:
    """Manages human-in-the-loop approval gate logic.

    This class handles the decision logic for gates.  The actual
    signal waiting happens in the Temporal workflow
    (``SDLCPipelineWorkflow``).

    All methods are static -- no instance state is needed.
    """

    @staticmethod
    def should_gate(gate_config: GateConfig) -> bool:
        """Determine if a phase should pause for human approval.

        A gate is active when:
        - ``mandatory`` is True (always gates, regardless of ``enabled``), or
        - ``enabled`` is True.

        Args:
            gate_config: Gate configuration for the phase.

        Returns:
            True if the pipeline should pause at this gate.
        """
        if gate_config.mandatory:
            return True
        return gate_config.enabled

    @staticmethod
    def build_gate_id(phase_name: str) -> str:
        """Create a deterministic gate ID from a phase name.

        Args:
            phase_name: Human-readable phase name.

        Returns:
            Gate identifier in the format ``"gate_{phase_name}"``.
        """
        return f"gate_{phase_name}"

    @staticmethod
    def resolve_timeout(gate_config: GateConfig) -> str:
        """Determine what happens when a gate times out.

        Args:
            gate_config: Gate configuration for the phase.

        Returns:
            The timeout action string (``"auto_approve"`` or ``"pause"``).
        """
        return gate_config.timeout_action
