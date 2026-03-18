"""Pipeline configuration and orchestration subsystem.

Public API:
    - :class:`PipelineConfig` -- top-level pipeline preset model
    - :class:`PhaseConfig` -- per-phase configuration
    - :class:`GateConfig` -- human approval gate settings
    - :class:`PipelineSettings` -- global pipeline settings
    - :func:`load_preset` -- load a YAML preset by name
    - :func:`detect_project_type` -- classify project as greenfield/inflight/brownfield
    - :func:`adapt_pipeline_for_project_type` -- filter phases by project type
"""

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

__all__ = [
    "GateConfig",
    "PhaseConfig",
    "PipelineConfig",
    "PipelineSettings",
    "adapt_pipeline_for_project_type",
    "detect_project_type",
    "load_preset",
]
