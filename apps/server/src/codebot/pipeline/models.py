"""Pydantic v2 models for pipeline configuration.

Defines the typed schema for pipeline presets (full, quick, review-only)
loaded from YAML files. All downstream pipeline orchestration depends on
these models for well-typed configuration.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class GateConfig(BaseModel):
    """Configuration for a human approval gate on a pipeline phase.

    Attributes:
        enabled: Whether the gate is active for this phase.
        prompt: Message displayed to the approver.
        timeout_minutes: How long to wait for approval before timeout_action.
        timeout_action: What happens on timeout -- ``"auto_approve"`` or ``"pause"``.
        mandatory: If True, timeout cannot auto-approve (always pauses).
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    prompt: str = ""
    timeout_minutes: int = 30
    timeout_action: str = "auto_approve"
    mandatory: bool = False


class PhaseConfig(BaseModel):
    """Configuration for a single pipeline phase (SDLC stage).

    Attributes:
        name: Human-readable phase name (e.g. ``"design"``, ``"implement"``).
        agents: List of agent identifiers to execute in this phase.
        sequential: If True agents run one-by-one; if False they run in parallel.
        human_gate: Gate configuration for human approval after this phase.
        on_failure: Strategy when a phase fails -- ``"escalate"`` or
            ``"reroute_to_implement"``.
        loop: Optional loop configuration (condition + max_iterations).
        skip_for_project_types: Project types for which this phase is skipped.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    agents: list[str]
    sequential: bool = True
    human_gate: GateConfig = GateConfig()
    on_failure: str = "escalate"
    loop: dict[str, object] | None = None
    skip_for_project_types: list[str] = []

    @property
    def parallel(self) -> bool:
        """Whether agents in this phase execute in parallel."""
        return not self.sequential


class PipelineSettings(BaseModel):
    """Global settings that apply across all phases of a pipeline.

    Attributes:
        max_parallel_agents: Maximum number of agents running concurrently.
        checkpoint_after_each_phase: Whether to checkpoint state after each phase.
        cost_limit_usd: Maximum USD spend before the pipeline pauses.
        timeout_minutes: Overall pipeline timeout.
    """

    model_config = ConfigDict(frozen=True)

    max_parallel_agents: int = 5
    checkpoint_after_each_phase: bool = True
    cost_limit_usd: float = 50.0
    timeout_minutes: int = 120


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration loaded from a YAML preset.

    Attributes:
        name: Preset name (e.g. ``"full-sdlc"``, ``"quick"``).
        version: Semantic version of the preset schema.
        description: Human-readable description.
        settings: Global pipeline settings.
        phases: Ordered list of phase configurations.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    version: str
    description: str = ""
    settings: PipelineSettings = PipelineSettings()
    phases: list[PhaseConfig]

    @field_validator("phases")
    @classmethod
    def validate_phases_not_empty(cls, v: list[PhaseConfig]) -> list[PhaseConfig]:
        """Ensure that a pipeline has at least one phase."""
        if not v:
            raise ValueError("Pipeline must have at least one phase")
        return v
