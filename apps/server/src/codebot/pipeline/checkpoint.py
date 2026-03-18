"""Pipeline data transfer objects for Temporal activity boundaries.

These dataclasses are JSON-serializable and designed to cross Temporal
activity/workflow boundaries cleanly.  They carry only primitive types
(``str``, ``int``, ``float``, ``bool``, ``list[dict]``, ``dict``) so that
Temporal's default JSON data converter handles them without custom codecs.

Classes:
    PipelineInput: Input to the top-level SDLC pipeline workflow.
    PhaseInput: Input to a single-phase execution activity.
    PhaseResult: Output from a single-phase execution activity.
    PipelineCheckpoint: Snapshot of pipeline progress for resume/continue-as-new.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class PipelineInput:
    """Input to the SDLC pipeline workflow.

    Attributes:
        project_id: Unique identifier for the project being processed.
        preset_name: Pipeline preset to load (``"full"``, ``"quick"``, ``"review-only"``).
        project_type: Detected project classification (``"greenfield"``, ``"inflight"``, etc.).
        resume_from_phase: If resuming, the phase index to start from.
    """

    project_id: str
    preset_name: str
    project_type: str
    resume_from_phase: int | None = None


@dataclass(slots=True, kw_only=True)
class PhaseInput:
    """Input to a single pipeline phase activity.

    Attributes:
        project_id: Unique identifier for the project being processed.
        phase_name: Human-readable name of the phase (e.g. ``"design"``).
        phase_idx: Zero-based index of this phase in the pipeline.
        agents: List of agent identifiers to execute in this phase.
        parallel: Whether agents should run concurrently.
        config: Serialized phase configuration dictionary.
    """

    project_id: str
    phase_name: str
    phase_idx: int
    agents: list[str]
    parallel: bool
    config: dict  # type: ignore[type-arg]


@dataclass(slots=True, kw_only=True)
class PhaseResult:
    """Result from a single pipeline phase execution.

    Attributes:
        phase_name: Human-readable name of the phase.
        phase_idx: Zero-based index of the phase.
        status: Outcome -- ``"completed"``, ``"failed"``, or ``"skipped"``.
        agent_results: Per-agent result dictionaries.
        duration_ms: Wall-clock execution time in milliseconds.
        tokens_used: Total LLM tokens consumed during the phase.
        cost_usd: Total USD cost of LLM usage in this phase.
    """

    phase_name: str
    phase_idx: int
    status: str  # "completed" | "failed" | "skipped"
    agent_results: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
    duration_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0


@dataclass(slots=True, kw_only=True)
class PipelineCheckpoint:
    """Snapshot of pipeline progress for resume and continue-as-new.

    Attributes:
        project_id: Unique identifier for the project being processed.
        preset_name: Pipeline preset that was loaded.
        project_type: Detected project classification.
        completed_phase_idx: Index of the last successfully completed phase.
        phase_results: Accumulated per-phase result dictionaries.
    """

    project_id: str
    preset_name: str
    project_type: str
    completed_phase_idx: int
    phase_results: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
