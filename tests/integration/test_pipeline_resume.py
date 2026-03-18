"""Integration tests for pipeline resume behavior.

Tests verify that resume_from_phase correctly skips already-completed
phases and produces accurate phases_completed counts.
"""

from __future__ import annotations

import uuid

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult, PipelineInput

# ---------------------------------------------------------------------------
# Stub activities for resume tests
# ---------------------------------------------------------------------------

RESUME_EXECUTED: list[str] = []


@activity.defn(name="load_pipeline_config")
async def resume_load_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a 6-phase config matching an SDLC subset for resume tests."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "init", "agents": ["initializer"], "sequential": True},
            {"name": "brainstorm", "agents": ["brainstormer"], "sequential": True},
            {"name": "research", "agents": ["researcher"], "sequential": True},
            {"name": "design", "agents": ["architect"], "sequential": True},
            {"name": "implement", "agents": ["backend_dev"], "sequential": True},
            {"name": "qa", "agents": ["qa_lead"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def resume_execute_phase(phase_input: PhaseInput) -> PhaseResult:
    """Track resumed phase execution."""
    RESUME_EXECUTED.append(phase_input.phase_name)
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
    )


@activity.defn(name="emit_pipeline_event")
async def resume_emit_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """No-op event emitter."""


_UNSANDBOXED = UnsandboxedWorkflowRunner()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipelineResume:
    """Tests for pipeline checkpoint/resume behavior."""

    async def test_resume_from_phase_3_skips_first_3(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Pipeline with resume_from_phase=3 skips phases 0, 1, 2."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        RESUME_EXECUTED.clear()
        task_queue = f"resume-{uuid.uuid4().hex[:8]}"

        async with Worker(
            temporal_env.client,
            task_queue=task_queue,
            workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
            activities=[
                resume_load_config,
                resume_execute_phase,
                resume_emit_event,
            ],
            workflow_runner=_UNSANDBOXED,
        ):
            result = await temporal_env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(
                    project_id="resume-test",
                    preset_name="full",
                    project_type="greenfield",
                    resume_from_phase=3,
                ),
                id=f"resume-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )

        assert result["status"] == "completed"
        # Phases 0 (init), 1 (brainstorm), 2 (research) should be skipped
        assert "init" not in RESUME_EXECUTED
        assert "brainstorm" not in RESUME_EXECUTED
        assert "research" not in RESUME_EXECUTED
        # Phases 3, 4, 5 should execute
        assert "design" in RESUME_EXECUTED
        assert "implement" in RESUME_EXECUTED
        assert "qa" in RESUME_EXECUTED

    async def test_resume_produces_correct_phases_completed_count(
        self, temporal_env: WorkflowEnvironment
    ) -> None:
        """Pipeline resume produces correct phases_completed count."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        RESUME_EXECUTED.clear()
        task_queue = f"resume-cnt-{uuid.uuid4().hex[:8]}"

        async with Worker(
            temporal_env.client,
            task_queue=task_queue,
            workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
            activities=[
                resume_load_config,
                resume_execute_phase,
                resume_emit_event,
            ],
            workflow_runner=_UNSANDBOXED,
        ):
            result = await temporal_env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(
                    project_id="resume-cnt-test",
                    preset_name="full",
                    project_type="greenfield",
                    resume_from_phase=4,
                ),
                id=f"resume-cnt-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )

        assert result["status"] == "completed"
        # Only phases 4 (implement) and 5 (qa) execute
        assert result["phases_completed"] == 2
        assert RESUME_EXECUTED == ["implement", "qa"]
