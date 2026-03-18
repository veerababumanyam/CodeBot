"""Temporal activities for pipeline orchestration.

Activities define the Temporal activity boundary -- all non-deterministic
operations (I/O, timers, external calls) must live inside activities, not
workflow functions.

Activities:
    load_pipeline_config: Load a YAML pipeline preset and return serialized config.
    execute_phase_activity: Execute a single pipeline phase with heartbeating.
    emit_pipeline_event: Emit a pipeline event (NATS integration wired in Plan 03).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from temporalio import activity

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult
from codebot.pipeline.loader import load_preset


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
async def execute_phase_activity(input: PhaseInput) -> PhaseResult:
    """Execute a single pipeline phase.

    In the full implementation, this delegates to the graph engine
    and agent registry.  For now, it provides the activity shell
    with heartbeating and timing.

    Args:
        input: Phase execution parameters.

    Returns:
        A :class:`PhaseResult` with per-agent results and timing.
    """
    start_ms = int(time.monotonic() * 1000)
    activity.heartbeat(f"Starting phase: {input.phase_name}")

    # TODO: Phase 2/3 integration -- delegate to graph engine
    agent_results: list[dict] = []  # type: ignore[type-arg]

    for agent_name in input.agents:
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
        phase_name=input.phase_name,
        phase_idx=input.phase_idx,
        status="completed",
        agent_results=agent_results,
        duration_ms=elapsed_ms,
        tokens_used=0,
        cost_usd=0.0,
    )


@activity.defn
async def emit_pipeline_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """Emit a pipeline event.

    In the full implementation, this publishes to NATS JetStream.
    Plan 03 adds the NATS integration.  This activity provides
    the Temporal activity boundary now.

    Args:
        event_data: Event payload dictionary with at least a ``"type"`` key.
    """
    activity.heartbeat(f"Emitting event: {event_data.get('type', 'unknown')}")
    # TODO: Plan 03 wires NATS JetStream here
    timestamp = datetime.now(timezone.utc).isoformat()
    activity.logger.info(
        "Pipeline event: type=%s timestamp=%s",
        event_data.get("type", "unknown"),
        timestamp,
    )
