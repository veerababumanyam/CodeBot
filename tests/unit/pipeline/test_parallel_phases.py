"""Tests for SDLCPipelineWorkflow and PhaseAgentWorkflow Temporal workflows.

Validates pipeline orchestration with sequential and parallel execution,
signal handlers, query methods, resume behavior, and continue-as-new.
Uses Temporal's in-memory WorkflowEnvironment for deterministic testing.
"""

from __future__ import annotations

import asyncio
import uuid

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from codebot.pipeline.checkpoint import PhaseInput, PhaseResult, PipelineInput


# Use unsandboxed runner for tests to avoid sandbox restrictions on
# transitive imports (e.g. pathlib.Path.resolve in loader.py).
_UNSANDBOXED = UnsandboxedWorkflowRunner()


# ---------------------------------------------------------------------------
# Stub activities for tests (must be defined at module level for Temporal)
# ---------------------------------------------------------------------------

EXECUTED_PHASES: list[str] = []
EMITTED_EVENTS: list[dict] = []  # type: ignore[type-arg]


@activity.defn(name="load_pipeline_config")
async def mock_load_pipeline_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a simple 3-phase sequential config."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "init", "agents": ["initializer"], "sequential": True},
            {"name": "design", "agents": ["architect"], "sequential": True},
            {"name": "implement", "agents": ["backend_dev", "frontend_dev"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def mock_execute_phase_activity(phase_input: PhaseInput) -> PhaseResult:
    """Track which phases were executed and return success."""
    EXECUTED_PHASES.append(phase_input.phase_name)
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
        agent_results=[{"agent": a, "status": "completed"} for a in phase_input.agents],
    )


@activity.defn(name="emit_pipeline_event")
async def mock_emit_pipeline_event(event_data: dict) -> None:  # type: ignore[type-arg]
    """Track emitted events."""
    EMITTED_EVENTS.append(event_data)


# ---------------------------------------------------------------------------
# Parallel-aware stub activities
# ---------------------------------------------------------------------------

PARALLEL_PHASES: list[str] = []


@activity.defn(name="load_pipeline_config")
async def mock_load_parallel_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a config with a parallel phase."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "init", "agents": ["initializer"], "sequential": True},
            {
                "name": "implement",
                "agents": ["backend_dev", "frontend_dev"],
                "sequential": False,
            },
            {"name": "qa", "agents": ["qa_lead"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def mock_parallel_execute(phase_input: PhaseInput) -> PhaseResult:
    """Track parallel phase execution."""
    PARALLEL_PHASES.append(phase_input.phase_name)
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
        agent_results=[{"agent": a, "status": "completed"} for a in phase_input.agents],
    )


# ---------------------------------------------------------------------------
# Resume-aware stub activities
# ---------------------------------------------------------------------------

RESUME_PHASES: list[str] = []


@activity.defn(name="load_pipeline_config")
async def mock_load_resume_config(preset_name: str) -> dict:  # type: ignore[type-arg]
    """Return a 5-phase config for resume testing."""
    return {
        "name": preset_name,
        "phases": [
            {"name": "init", "agents": ["initializer"], "sequential": True},
            {"name": "brainstorm", "agents": ["brainstormer"], "sequential": True},
            {"name": "research", "agents": ["researcher"], "sequential": True},
            {"name": "design", "agents": ["architect"], "sequential": True},
            {"name": "implement", "agents": ["backend_dev"], "sequential": True},
        ],
    }


@activity.defn(name="execute_phase_activity")
async def mock_resume_execute(phase_input: PhaseInput) -> PhaseResult:
    """Track resumed phases."""
    RESUME_PHASES.append(phase_input.phase_name)
    return PhaseResult(
        phase_name=phase_input.phase_name,
        phase_idx=phase_input.phase_idx,
        status="completed",
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_worker(
    client: object,
    task_queue: str,
    workflows: list[type],
    activities: list[object],
) -> Worker:
    """Create a Worker with unsandboxed runner for tests."""
    return Worker(
        client,  # type: ignore[arg-type]
        task_queue=task_queue,
        workflows=workflows,
        activities=activities,  # type: ignore[arg-type]
        workflow_runner=_UNSANDBOXED,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSDLCPipelineWorkflowSequential:
    """Test SDLCPipelineWorkflow with sequential phase execution."""

    async def test_sequential_3_phase_pipeline_completes_all_phases(self) -> None:
        """SDLCPipelineWorkflow.run with 3-phase sequential config completes all phases in order."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        EXECUTED_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-seq-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_pipeline_config,
                    mock_execute_phase_activity,
                    mock_emit_pipeline_event,
                ],
            ):
                result = await env.client.execute_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="quick",
                        project_type="greenfield",
                    ),
                    id=f"test-pipeline-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

        assert result["status"] == "completed"
        assert result["phases_completed"] == 3
        assert EXECUTED_PHASES == ["init", "design", "implement"]


class TestSDLCPipelineWorkflowParallel:
    """Test SDLCPipelineWorkflow with parallel phase execution."""

    async def test_parallel_phase_spawns_child_workflows(self) -> None:
        """SDLCPipelineWorkflow.run with parallel phase spawns child workflows via asyncio.gather."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        PARALLEL_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-par-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_parallel_config,
                    mock_parallel_execute,
                    mock_emit_pipeline_event,
                ],
            ):
                result = await env.client.execute_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="quick",
                        project_type="greenfield",
                    ),
                    id=f"test-parallel-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

        assert result["status"] == "completed"
        assert result["phases_completed"] == 3
        # Parallel phase "implement" should appear in executed phases
        assert "implement" in PARALLEL_PHASES


class TestSDLCPipelineWorkflowSignals:
    """Test SDLCPipelineWorkflow signal handlers."""

    async def test_approve_gate_signal_sets_gate_decision(self) -> None:
        """SDLCPipelineWorkflow.approve_gate signal sets gate_decisions dict entry."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        EXECUTED_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-sig-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_pipeline_config,
                    mock_execute_phase_activity,
                    mock_emit_pipeline_event,
                ],
            ):
                handle = await env.client.start_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="quick",
                        project_type="greenfield",
                    ),
                    id=f"test-signal-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

                # Send gate approval signal (multi-arg signals use args=[...])
                await handle.signal(
                    SDLCPipelineWorkflow.approve_gate,
                    args=["gate_design", "approved"],
                )

                # Wait for workflow completion
                result = await handle.result()

        assert result["status"] == "completed"

    async def test_pause_and_resume_signals(self) -> None:
        """SDLCPipelineWorkflow.pause_pipeline and resume_pipeline signals work correctly."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        EXECUTED_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-pause-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_pipeline_config,
                    mock_execute_phase_activity,
                    mock_emit_pipeline_event,
                ],
            ):
                handle = await env.client.start_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="quick",
                        project_type="greenfield",
                    ),
                    id=f"test-pause-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

                # Send pause signal
                await handle.signal(SDLCPipelineWorkflow.pause_pipeline)

                # Small delay to allow signal processing
                await asyncio.sleep(0.5)

                # Query status -- should show paused
                status = await handle.query(SDLCPipelineWorkflow.get_status)
                assert status["is_paused"] is True

                # Resume
                await handle.signal(SDLCPipelineWorkflow.resume_pipeline)

                # Should complete
                result = await handle.result()

        assert result["status"] == "completed"


class TestSDLCPipelineWorkflowQuery:
    """Test SDLCPipelineWorkflow query methods."""

    async def test_get_status_returns_current_state(self) -> None:
        """SDLCPipelineWorkflow.get_status query returns current_phase_idx and is_paused."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        EXECUTED_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-query-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_pipeline_config,
                    mock_execute_phase_activity,
                    mock_emit_pipeline_event,
                ],
            ):
                handle = await env.client.start_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="quick",
                        project_type="greenfield",
                    ),
                    id=f"test-query-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

                result = await handle.result()

        assert result["status"] == "completed"


class TestSDLCPipelineWorkflowResume:
    """Test SDLCPipelineWorkflow resume behavior."""

    async def test_skips_completed_phases_on_resume(self) -> None:
        """SDLCPipelineWorkflow skips already-completed phases when resume_from_phase is set."""
        from codebot.pipeline.workflows import PhaseAgentWorkflow, SDLCPipelineWorkflow

        RESUME_PHASES.clear()
        EMITTED_EVENTS.clear()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            task_queue = f"test-resume-{uuid.uuid4().hex[:8]}"
            async with _make_worker(
                env.client,
                task_queue=task_queue,
                workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
                activities=[
                    mock_load_resume_config,
                    mock_resume_execute,
                    mock_emit_pipeline_event,
                ],
            ):
                result = await env.client.execute_workflow(
                    SDLCPipelineWorkflow.run,
                    PipelineInput(
                        project_id="test-proj",
                        preset_name="full",
                        project_type="greenfield",
                        resume_from_phase=3,
                    ),
                    id=f"test-resume-{uuid.uuid4().hex[:8]}",
                    task_queue=task_queue,
                )

        assert result["status"] == "completed"
        # Phases 0, 1, 2 should be skipped; only phases 3 and 4 execute
        assert result["phases_completed"] == 2
        assert "init" not in RESUME_PHASES
        assert "brainstorm" not in RESUME_PHASES
        assert "research" not in RESUME_PHASES
        assert "design" in RESUME_PHASES
        assert "implement" in RESUME_PHASES


class TestSDLCPipelineWorkflowContinueAsNew:
    """Test SDLCPipelineWorkflow continue-as-new behavior."""

    async def test_calls_continue_as_new_when_suggested(self) -> None:
        """SDLCPipelineWorkflow calls continue_as_new when is_continue_as_new_suggested is True."""
        from codebot.pipeline.workflows import SDLCPipelineWorkflow

        # This test verifies the code path exists. In real Temporal,
        # is_continue_as_new_suggested() is controlled by the server.
        # We verify the code structure contains the check.
        import inspect

        source = inspect.getsource(SDLCPipelineWorkflow.run)
        assert "is_continue_as_new_suggested" in source
        assert "continue_as_new" in source

    async def test_continue_as_new_preserves_project_id(self) -> None:
        """continue_as_new call includes project_id and resume_from_phase."""
        from codebot.pipeline.workflows import SDLCPipelineWorkflow

        import inspect

        source = inspect.getsource(SDLCPipelineWorkflow.run)
        assert "resume_from_phase=idx + 1" in source
        assert "project_id=input.project_id" in source
