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
    - :class:`PipelineEvent` -- typed pipeline event dataclass
    - :class:`PipelineEventEmitter` -- NATS JetStream event publisher
    - :func:`create_worker` -- build a configured Temporal Worker
    - :func:`run_worker` -- connect to Temporal and run the worker
"""

from codebot.pipeline.events import PipelineEvent, PipelineEventEmitter
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
from codebot.pipeline.worker import create_worker, run_worker

__all__ = [
    "GateConfig",
    "PhaseConfig",
    "PhaseInput",
    "PhaseRegistry",
    "PhaseResult",
    "PipelineCheckpoint",
    "PipelineConfig",
    "PipelineEvent",
    "PipelineEventEmitter",
    "PipelineInput",
    "PipelineSettings",
    "adapt_pipeline_for_project_type",
    "create_worker",
    "detect_project_type",
    "load_preset",
    "run_worker",
]
