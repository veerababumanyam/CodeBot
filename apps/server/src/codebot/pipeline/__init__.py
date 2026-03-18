"""Pipeline configuration and orchestration subsystem.

Public API:
    - :class:`PipelineConfig` -- top-level pipeline preset model
    - :class:`PhaseConfig` -- per-phase configuration
    - :class:`GateConfig` -- human approval gate settings
    - :class:`PipelineSettings` -- global pipeline settings
    - :class:`PipelineInput` -- workflow input DTO
    - :class:`PhaseInput` -- activity input DTO
    - :class:`PhaseResult` -- activity output DTO
    - :class:`PipelineCheckpoint` -- resume/continue-as-new snapshot
    - :class:`PhaseRegistry` -- phase-to-agent mapping registry
    - :func:`load_preset` -- load a YAML preset by name
    - :func:`detect_project_type` -- classify project as greenfield/inflight/brownfield
    - :func:`adapt_pipeline_for_project_type` -- filter phases by project type
"""

from codebot.pipeline.checkpoint import (
    PhaseInput,
    PhaseResult,
    PipelineCheckpoint,
    PipelineInput,
)
from codebot.pipeline.loader import load_preset
from codebot.pipeline.models import (
    GateConfig,
    PhaseConfig,
    PipelineConfig,
    PipelineSettings,
)
from codebot.pipeline.project_detector import (
    adapt_pipeline_for_project_type,
    detect_project_type,
)
from codebot.pipeline.registry import PhaseRegistry

__all__ = [
    "GateConfig",
    "PhaseConfig",
    "PhaseInput",
    "PhaseRegistry",
    "PhaseResult",
    "PipelineCheckpoint",
    "PipelineConfig",
    "PipelineInput",
    "PipelineSettings",
    "adapt_pipeline_for_project_type",
    "detect_project_type",
    "load_preset",
]
