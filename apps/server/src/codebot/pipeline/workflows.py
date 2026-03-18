"""Temporal workflow definitions for SDLC pipeline orchestration.

Two workflows compose the pipeline:

:class:`SDLCPipelineWorkflow`
    Top-level durable workflow that orchestrates all SDLC stages (S0-S9).
    Supports sequential and parallel execution, human approval gates via
    signals, pause/resume control, crash recovery via Temporal replay,
    and ``continue-as-new`` for event history management.

:class:`PhaseAgentWorkflow`
    Child workflow spawned for each agent during parallel phase execution.
    Provides per-agent durability and independent retry.

Workflow code is deterministic -- all I/O is delegated to activities
defined in :mod:`codebot.pipeline.activities`.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from codebot.pipeline.activities import (
        emit_pipeline_event,
        execute_phase_activity,
        load_pipeline_config,
    )
    from codebot.pipeline.checkpoint import (
        PhaseInput,
        PhaseResult,
        PipelineInput,
    )
    from codebot.pipeline.gates import GateManager
    from codebot.pipeline.models import GateConfig

# ---------------------------------------------------------------------------
# Retry policies per activity type
# ---------------------------------------------------------------------------

FAST_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
)

AGENT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=3,
)


@workflow.defn
class PhaseAgentWorkflow:
    """Child workflow for executing a single agent within a parallel phase.

    Each child workflow wraps the ``execute_phase_activity`` Temporal activity
    with per-agent durability.  If the activity fails, Temporal retries it
    independently of other agents in the same parallel phase.
    """

    @workflow.run
    async def run(self, input: PhaseInput) -> PhaseResult:
        """Execute a single agent's phase activity.

        Args:
            input: Phase execution parameters scoped to one agent.

        Returns:
            The :class:`PhaseResult` from the activity.
        """
        return await workflow.execute_activity(
            execute_phase_activity,
            input,
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=AGENT_RETRY,
        )


@workflow.defn
class SDLCPipelineWorkflow:
    """Top-level durable SDLC pipeline workflow.

    Orchestrates the 10-stage pipeline (S0-S9) with:

    - **Sequential and parallel phase execution:** Sequential phases use
      a single ``execute_phase_activity``.  Parallel phases spawn one
      :class:`PhaseAgentWorkflow` child workflow per agent and gather results.
    - **Human approval gates:** Signals set ``gate_decisions``; the workflow
      waits via ``workflow.wait_condition`` with a configurable timeout.
    - **Pause/resume:** ``pause_pipeline`` / ``resume_pipeline`` signals.
    - **Crash recovery:** Temporal automatically replays the workflow on crash.
    - **Continue-as-new:** When ``is_continue_as_new_suggested()`` fires, the
      workflow chains forward with ``resume_from_phase`` set to skip completed
      phases.
    """

    def __init__(self) -> None:
        self.gate_decisions: dict[str, str] = {}
        self.current_phase_idx: int = 0
        self.is_paused: bool = False

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    @workflow.signal
    async def approve_gate(
        self,
        gate_id: str,
        decision: str,
        feedback: str = "",
    ) -> None:
        """Record a human gate decision.

        Args:
            gate_id: Identifier for the gate (e.g. ``"gate_design"``).
            decision: Outcome -- ``"approved"`` or ``"rejected"``.
            feedback: Optional human feedback text.
        """
        self.gate_decisions[gate_id] = decision

    @workflow.signal
    async def pause_pipeline(self) -> None:
        """Pause the pipeline. Execution resumes when ``resume_pipeline`` is signalled."""
        self.is_paused = True

    @workflow.signal
    async def resume_pipeline(self) -> None:
        """Resume a paused pipeline."""
        self.is_paused = False

    # ------------------------------------------------------------------
    # Query handler
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> dict:  # type: ignore[type-arg]
        """Return the current pipeline status.

        Returns:
            Dictionary with ``current_phase_idx``, ``is_paused``, and
            ``gate_decisions``.
        """
        return {
            "current_phase_idx": self.current_phase_idx,
            "is_paused": self.is_paused,
            "gate_decisions": dict(self.gate_decisions),
        }

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, input: PipelineInput) -> dict:  # type: ignore[type-arg]
        """Execute the SDLC pipeline end-to-end.

        Args:
            input: Pipeline execution parameters.

        Returns:
            Summary dictionary with ``status``, ``phases_completed``, and
            ``results`` list.
        """
        # Load config via activity (non-deterministic I/O)
        config = await workflow.execute_activity(
            load_pipeline_config,
            input.preset_name,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=FAST_RETRY,
        )

        phases: list[dict] = config["phases"]  # type: ignore[assignment]
        start_idx = input.resume_from_phase or 0
        results: list[dict] = []  # type: ignore[type-arg]

        for idx, phase in enumerate(phases):
            if idx < start_idx:
                continue

            self.current_phase_idx = idx

            # Respect pause signals
            await workflow.wait_condition(lambda: not self.is_paused)

            # Emit phase-start event
            await workflow.execute_activity(
                emit_pipeline_event,
                {
                    "type": "phase.started",
                    "phase": phase["name"],
                    "phase_idx": idx,
                },
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=FAST_RETRY,
            )

            # Execute phase (parallel or sequential)
            if not phase.get("sequential", True):
                result = await self._execute_parallel_phase(
                    input.project_id, phase, idx
                )
            else:
                result = await self._execute_sequential_phase(
                    input.project_id, phase, idx
                )

            results.append(
                {
                    "phase_name": result.phase_name,
                    "phase_idx": result.phase_idx,
                    "status": result.status,
                }
            )

            # Human gate check (delegates to GateManager from Plan 02)
            gate_cfg = phase.get("human_gate", {})
            gate_config = GateConfig(**gate_cfg) if gate_cfg else GateConfig()
            if GateManager.should_gate(gate_config):
                gate_id = GateManager.build_gate_id(phase["name"])
                timeout_action = GateManager.resolve_timeout(gate_config)
                gate_result = await self._wait_for_gate(
                    gate_id=gate_id,
                    timeout_minutes=gate_config.timeout_minutes,
                    timeout_action=timeout_action,
                )

                await workflow.execute_activity(
                    emit_pipeline_event,
                    {
                        "type": "gate.decided",
                        "gate_id": gate_id,
                        "decision": gate_result,
                    },
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=FAST_RETRY,
                )

            # Emit phase-complete event
            await workflow.execute_activity(
                emit_pipeline_event,
                {
                    "type": "phase.completed",
                    "phase": phase["name"],
                    "phase_idx": idx,
                },
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=FAST_RETRY,
            )

            # Continue-as-new for event history management
            if workflow.info().is_continue_as_new_suggested():
                await workflow.wait_condition(workflow.all_handlers_finished)
                workflow.continue_as_new(
                    PipelineInput(
                        project_id=input.project_id,
                        preset_name=input.preset_name,
                        project_type=input.project_type,
                        resume_from_phase=idx + 1,
                    )
                )

        return {
            "status": "completed",
            "phases_completed": len(results),
            "results": results,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _execute_sequential_phase(
        self,
        project_id: str,
        phase: dict,  # type: ignore[type-arg]
        idx: int,
    ) -> PhaseResult:
        """Execute a phase sequentially via a single activity.

        Args:
            project_id: Current project identifier.
            phase: Phase configuration dictionary.
            idx: Zero-based phase index.

        Returns:
            The :class:`PhaseResult` from the activity.
        """
        return await workflow.execute_activity(
            execute_phase_activity,
            PhaseInput(
                project_id=project_id,
                phase_name=phase["name"],
                phase_idx=idx,
                agents=phase.get("agents", []),
                parallel=False,
                config=phase,
            ),
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=AGENT_RETRY,
        )

    async def _execute_parallel_phase(
        self,
        project_id: str,
        phase: dict,  # type: ignore[type-arg]
        idx: int,
    ) -> PhaseResult:
        """Execute a phase in parallel via child workflows.

        Each agent gets its own :class:`PhaseAgentWorkflow` child workflow.
        Results are collected with ``asyncio.gather``.

        Args:
            project_id: Current project identifier.
            phase: Phase configuration dictionary.
            idx: Zero-based phase index.

        Returns:
            A merged :class:`PhaseResult` with all agent results.
        """
        agents: list[str] = phase.get("agents", [])
        if not agents:
            return PhaseResult(
                phase_name=phase["name"],
                phase_idx=idx,
                status="completed",
            )

        child_handles = []
        for agent in agents:
            handle = await workflow.start_child_workflow(
                PhaseAgentWorkflow.run,
                PhaseInput(
                    project_id=project_id,
                    phase_name=phase["name"],
                    phase_idx=idx,
                    agents=[agent],
                    parallel=False,
                    config=phase,
                ),
                id=f"phase-{idx}-agent-{agent}-{workflow.uuid4()}",
            )
            child_handles.append(handle)

        child_results = await asyncio.gather(*child_handles)
        return PhaseResult(
            phase_name=phase["name"],
            phase_idx=idx,
            status="completed",
            agent_results=[
                {"agent": a, "status": r.status}
                for a, r in zip(agents, child_results, strict=False)
            ],
        )

    async def _wait_for_gate(
        self,
        gate_id: str,
        timeout_minutes: int,
        timeout_action: str,
    ) -> str:
        """Wait for a human approval gate decision.

        Args:
            gate_id: Deterministic gate identifier.
            timeout_minutes: How long to wait before applying timeout_action.
            timeout_action: What to do on timeout (``"auto_approve"`` or ``"pause"``).

        Returns:
            The gate decision string.
        """
        await workflow.execute_activity(
            emit_pipeline_event,
            {"type": "gate.waiting", "gate_id": gate_id},
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=FAST_RETRY,
        )
        try:
            await workflow.wait_condition(
                lambda: gate_id in self.gate_decisions,
                timeout=timedelta(minutes=timeout_minutes),
            )
            return self.gate_decisions[gate_id]
        except asyncio.TimeoutError:
            if timeout_action == "pause":
                self.is_paused = True
                await workflow.wait_condition(lambda: not self.is_paused)
                return self.gate_decisions.get(gate_id, "auto_approved")
            return "auto_approved"
