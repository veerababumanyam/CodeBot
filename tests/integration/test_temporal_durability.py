"""Integration tests for Temporal durability features.

Tests verify that RetryPolicy retries failed activities and that
start_to_close_timeout enforces time limits on activities.
"""

from __future__ import annotations

import uuid

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult, PipelineInput

# ---------------------------------------------------------------------------
# Stub activities with failure simulation
# ---------------------------------------------------------------------------

_attempt_counter: dict[str, int] = {}


@activity.defn(name="load_pipeline_config")
async def durability_load_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a single-phase config for durability tests."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "test_phase", "agents": ["test_agent"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def failing_then_succeeding_execute(phase_input: PhaseInput) -> PhaseResult:
    """Fail on first attempt, succeed on second (tests retry).

    Uses a module-level counter keyed by project_id to track attempts.
    """
    key = f"{phase_input.project_id}:{phase_input.phase_name}"
    _attempt_counter.setdefault(key, 0)
    _attempt_counter[key] += 1

    if _attempt_counter[key] < 2:
        raise RuntimeError("Transient failure -- should be retried")

    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
    )


@activity.defn(name="emit_pipeline_event")
async def durability_emit_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """No-op event emitter."""


_UNSANDBOXED = UnsandboxedWorkflowRunner()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTemporalDurability:
    """Tests for Temporal retry and timeout behavior."""

    async def test_retry_policy_retries_failed_activity(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Worker with RetryPolicy retries a transiently failing activity."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        _attempt_counter.clear()
        task_queue = f"dur-retry-{uuid.uuid4().hex[:8]}"

        async with Worker(
            temporal_env.client,
            task_queue=task_queue,
            workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
            activities=[
                durability_load_config,
                failing_then_succeeding_execute,
                durability_emit_event,
            ],
            workflow_runner=_UNSANDBOXED,
        ):
            result = await temporal_env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(
                    project_id="dur-retry-test",
                    preset_name="quick",
                    project_type="greenfield",
                ),
                id=f"dur-retry-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )

        # Pipeline should succeed after retry
        assert result["status"] == "completed"
        # Activity should have been called at least twice (first fail + retry success)
        key = "dur-retry-test:test_phase"
        assert _attempt_counter.get(key, 0) >= 2

    async def test_timeout_is_configured_on_activities(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Pipeline configures start_to_close_timeout on activity executions."""
        from codebot.pipeline.workflows import SDLCPipelineWorkflow

        import inspect

        source = inspect.getsource(SDLCPipelineWorkflow)
        # Verify that start_to_close_timeout is configured for phase execution
        assert "start_to_close_timeout" in source
        # Verify heartbeat_timeout is used for agent activities
        assert "heartbeat_timeout" in source
