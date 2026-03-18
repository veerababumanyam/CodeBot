"""End-to-end integration tests for the SDLC pipeline workflow.

Tests verify the full pipeline execution path using Temporal's in-memory
test server with time-skipping.  Activities are stubbed at the Temporal
level to avoid external service dependencies.
"""

from __future__ import annotations

import uuid

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult, PipelineInput

# ---------------------------------------------------------------------------
# Stub activities for E2E tests
# ---------------------------------------------------------------------------

E2E_PHASES_EXECUTED: list[str] = []


@activity.defn(name="load_pipeline_config")
async def e2e_load_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a quick preset with 5 phases (init, design, implement-parallel, qa, docs)."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "init", "agents": ["initializer"], "sequential": True},
            {"name": "design", "agents": ["architect", "designer"], "sequential": True},
            {
                "name": "implement",
                "agents": ["backend_dev", "frontend_dev"],
                "sequential": False,
            },
            {"name": "qa", "agents": ["qa_lead"], "sequential": True},
            {"name": "docs", "agents": ["doc_writer"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def e2e_execute_phase(phase_input: PhaseInput) -> PhaseResult:
    """Track and complete each phase."""
    E2E_PHASES_EXECUTED.append(phase_input.phase_name)
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
        agent_results=[{"agent": a, "status": "completed"} for a in phase_input.agents],
    )


@activity.defn(name="emit_pipeline_event")
async def e2e_emit_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """No-op event emitter for E2E tests."""


_UNSANDBOXED = UnsandboxedWorkflowRunner()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipelineE2E:
    """End-to-end pipeline integration tests."""

    async def test_full_pipeline_completes_all_phases(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Full pipeline with quick preset completes all phases and returns status completed."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        E2E_PHASES_EXECUTED.clear()
        task_queue = f"e2e-{uuid.uuid4().hex[:8]}"

        async with Worker(
            temporal_env.client,
            task_queue=task_queue,
            workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
            activities=[e2e_load_config, e2e_execute_phase, e2e_emit_event],
            workflow_runner=_UNSANDBOXED,
        ):
            result = await temporal_env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(
                    project_id="e2e-test",
                    preset_name="quick",
                    project_type="greenfield",
                ),
                id=f"e2e-pipeline-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )

        assert result["status"] == "completed"
        assert result["phases_completed"] == 5
        # "implement" appears twice because parallel phase spawns 2 child
        # workflows (one per agent), each calling execute_phase_activity.
        unique_phases = list(dict.fromkeys(E2E_PHASES_EXECUTED))
        assert unique_phases == ["init", "design", "implement", "qa", "docs"]

    async def test_pipeline_with_parallel_phase_collects_results(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Pipeline with parallel phase correctly spawns child workflows and collects results."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        E2E_PHASES_EXECUTED.clear()
        task_queue = f"e2e-par-{uuid.uuid4().hex[:8]}"

        async with Worker(
            temporal_env.client,
            task_queue=task_queue,
            workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
            activities=[e2e_load_config, e2e_execute_phase, e2e_emit_event],
            workflow_runner=_UNSANDBOXED,
        ):
            result = await temporal_env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(
                    project_id="e2e-par-test",
                    preset_name="quick",
                    project_type="greenfield",
                ),
                id=f"e2e-parallel-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )

        assert result["status"] == "completed"
        # The parallel phase "implement" should have agent_results
        implement_phase = next(
            r for r in result["results"] if r["phase_name"] == "implement"
        )
        assert implement_phase["status"] == "completed"
