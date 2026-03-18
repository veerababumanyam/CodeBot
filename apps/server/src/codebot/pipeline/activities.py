"""Temporal activities for pipeline orchestration.

Activities define the Temporal activity boundary -- all non-deterministic
operations (I/O, timers, external calls) must live inside activities, not
workflow functions.

Activities:
    load_pipeline_config: Load a YAML pipeline preset and return serialized config.
    execute_phase_activity: Execute a single pipeline phase with heartbeating.
    emit_pipeline_event: Emit a pipeline event to NATS JetStream (with logging fallback).

Functions:
    set_event_emitter: Set the shared PipelineEventEmitter singleton (called by worker on startup).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from temporalio import activity

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult
from codebot.pipeline.events import PipelineEventEmitter
from codebot.pipeline.loader import load_preset

logger = logging.getLogger(__name__)

# Module-level emitter singleton (set by worker on startup via set_event_emitter)
_emitter: PipelineEventEmitter | None = None


def set_event_emitter(emitter: PipelineEventEmitter) -> None:
    """Set the shared event emitter (called by worker on startup).

    This avoids creating a new NATS connection for every activity call.
    The worker initialises the NATS connection once and passes the
    emitter here before registering activities.

    Args:
        emitter: A fully initialised :class:`PipelineEventEmitter`.
    """
    global _emitter  # noqa: PLW0603
    _emitter = emitter


@activity.defn
async def load_pipeline_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Load pipeline configuration from a YAML preset.

    This is an activity because file I/O is non-deterministic
    and must not run inside a workflow function.

    Args:
        preset_name: Name of the preset (e.g. ``"full"``, ``"quick"``).

    Returns:
        Serialized :class:`PipelineConfig` as a dictionary.
    """
    config = load_preset(preset_name)
    return config.model_dump()


@activity.defn
async def execute_phase_activity(phase_input: PhaseInput) -> PhaseResult:
    """Execute a single pipeline phase.

    In the full implementation, this delegates to the graph engine
    and agent registry.  For now, it provides the activity shell
    with heartbeating and timing.

    Args:
        phase_input: Phase execution parameters.

    Returns:
        A :class:`PhaseResult` with per-agent results and timing.
    """
    start_ms = int(time.monotonic() * 1000)
    activity.heartbeat(f"Starting phase: {phase_input.phase_name}")

    # TODO: Phase 2/3 integration -- delegate to graph engine
    agent_results: list[dict] = []  # type: ignore[type-arg]

    for agent_name in phase_input.agents:
        activity.heartbeat(f"Executing agent: {agent_name}")
        agent_results.append(
            {
                "agent": agent_name,
                "status": "completed",
                "output": {},
            }
        )

    elapsed_ms = int(time.monotonic() * 1000) - start_ms
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
        agent_results=agent_results,
        duration_ms=elapsed_ms,
        tokens_used=0,
        cost_usd=0.0,
    )


@activity.defn
async def emit_pipeline_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """Emit a pipeline event to NATS JetStream.

    Uses the module-level singleton emitter set by :func:`set_event_emitter`.
    Falls back to logging when NATS is unavailable (graceful degradation).

    Args:
        event_data: Event payload dictionary with at least a ``"type"`` key.
    """
    event_type = event_data.get("type", "unknown")
    activity.heartbeat(f"Emitting event: {event_type}")

    if _emitter is not None:
        try:
            await _emitter.emit(event_type, event_data)
            return
        except Exception as exc:
            logger.warning("NATS emit failed, falling back to log: %s", exc)

    # Fallback: log the event when NATS is unavailable
    timestamp = datetime.now(UTC).isoformat()
    logger.info(
        "Pipeline event: type=%s timestamp=%s data=%s",
        event_type,
        timestamp,
        event_data,
    )
