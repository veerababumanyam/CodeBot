"""Pipeline configuration and orchestration subsystem.

Public API:
    - :class:`PipelineConfig` -- top-level pipeline preset model
    - :class:`PhaseConfig` -- per-phase configuration
    - :class:`GateConfig` -- human approval gate settings
    - :class:`PipelineSettings` -- global pipeline settings
    - :func:`load_preset` -- load a YAML preset by name
"""

from codebot.pipeline.loader import load_preset
from codebot.pipeline.models import (
    GateConfig,
    PhaseConfig,
    PipelineConfig,
    PipelineSettings,
)

__all__ = [
    "GateConfig",
    "PhaseConfig",
    "PipelineConfig",
    "PipelineSettings",
    "load_preset",
]
