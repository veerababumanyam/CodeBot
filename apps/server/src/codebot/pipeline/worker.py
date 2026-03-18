"""Temporal worker for the SDLC pipeline.

Starts a Temporal :class:`~temporalio.worker.Worker` with all pipeline
workflows and activities registered.  Optionally initializes the NATS
JetStream event emitter if the ``nats`` and ``events`` modules are
available (Plan 03 wires the full NATS integration).

Functions:
    create_worker: Build a configured Worker instance.
    run_worker: Connect to Temporal and run the worker until shutdown.

Usage::

    # As a standalone process
    python -m codebot.pipeline.worker

    # Programmatically
    from codebot.pipeline.worker import run_worker
    await run_worker()
"""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from codebot.pipeline.activities import (
    emit_pipeline_event,
    execute_phase_activity,
    load_pipeline_config,
    set_event_emitter,
)
from codebot.pipeline.events import PipelineEventEmitter
from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

logger = logging.getLogger(__name__)

TASK_QUEUE = "codebot-pipeline"


async def create_worker(
    client: Client,
    task_queue: str = TASK_QUEUE,
) -> Worker:
    """Create a Temporal worker with pipeline workflows and activities.

    Args:
        client: Connected Temporal client.
        task_queue: Temporal task queue name.  Defaults to
            ``"codebot-pipeline"``.

    Returns:
        A configured :class:`Worker` ready to be started with ``worker.run()``.
    """
    return Worker(
        client,
        task_queue=task_queue,
        workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
        activities=[
            load_pipeline_config,
            execute_phase_activity,
            emit_pipeline_event,
        ],
    )


async def run_worker(
    temporal_address: str = "localhost:7233",
    nats_url: str = "nats://localhost:4222",
    task_queue: str = TASK_QUEUE,
) -> None:
    """Connect to Temporal and run the pipeline worker.

    Also initializes the NATS JetStream event emitter if available.
    The NATS integration is best-effort -- the worker still runs if
    NATS is unavailable, but events will only be logged.

    Args:
        temporal_address: ``host:port`` of the Temporal frontend service.
        nats_url: NATS server URL for event emission.
        task_queue: Temporal task queue name.
    """
    client = await Client.connect(temporal_address)

    # Initialize NATS event emitter (graceful if unavailable).
    # The emitter is injected into the activities module via set_event_emitter
    # so every emit_pipeline_event activity call can publish to NATS.
    try:
        import nats as nats_lib  # noqa: PLC0415

        nc = await nats_lib.connect(nats_url)
        emitter = PipelineEventEmitter(nc)
        await emitter.ensure_stream()
        set_event_emitter(emitter)
        logger.info("NATS event emitter initialized")
    except Exception as exc:  # noqa: BLE001
        logger.warning("NATS unavailable, events will be logged only: %s", exc)

    worker = await create_worker(client, task_queue)
    logger.info("Starting pipeline worker on queue=%s", task_queue)
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
