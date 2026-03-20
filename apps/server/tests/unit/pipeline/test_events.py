from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from codebot.pipeline.events import PipelineEventEmitter


@pytest.mark.asyncio
async def test_emit_publishes_to_pipeline_and_event_bus_subjects() -> None:
    nc = MagicMock()
    js = AsyncMock()
    nc.jetstream.return_value = js

    emitter = PipelineEventEmitter(nc)
    await emitter.emit(
        "phase.started",
        {"pipeline_id": "pipe-1", "project_id": "proj-1", "phase": "planning"},
    )

    publish_calls = js.publish.await_args_list
    assert len(publish_calls) == 2
    assert publish_calls[0].args[0] == "pipeline.phase_started"
    assert publish_calls[1].args[0] == "codebot.events.phase.started"


@pytest.mark.asyncio
async def test_ensure_stream_creates_pipeline_and_event_bus_streams() -> None:
    nc = MagicMock()
    js = AsyncMock()
    nc.jetstream.return_value = js

    emitter = PipelineEventEmitter(nc)
    await emitter.ensure_stream()

    assert js.add_stream.await_count == 2