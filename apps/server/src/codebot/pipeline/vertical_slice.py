"""Vertical slice pipeline: 5-agent graph builder and executor.

Composes the 5 agents from Phase 7 (Orchestrator, BackendDev,
CodeReviewer, Tester, Debugger) into a sequential pipeline with
quality gate enforcement, test-failure-to-debugger routing, and
optional NATS event emission.

Public API:
    - :func:`build_vertical_slice_graph` -- factory that creates a configured pipeline
    - :class:`VerticalSlicePipeline` -- the pipeline executor
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput
from agent_sdk.models.enums import AgentType

from codebot.agents.backend_dev import BackendDevAgent
from codebot.agents.code_reviewer import CodeReviewerAgent
from codebot.agents.debugger import DebuggerAgent
from codebot.agents.orchestrator import OrchestratorAgent
from codebot.agents.tester import TesterAgent
from codebot.events.bus import EventBus
from codebot.pipeline.event_emitter import PipelineEventEmitter

logger = logging.getLogger(__name__)

_MAX_QA_REROUTES = 2


@dataclass(slots=True, kw_only=True)
class VerticalSlicePipeline:
    """Orchestrates the 5-agent vertical slice pipeline.

    Execution flow::

        Orchestrator -> BackendDev -> CodeReviewer -> Tester -> Debugger (conditional)

    The quality gate after CodeReviewer blocks advancement when
    ``gate_passed=False``, rerouting back to BackendDev (up to
    :data:`_MAX_QA_REROUTES` cycles). Failed tests from Tester
    route to Debugger via SharedState (TEST-05).

    Attributes:
        orchestrator: Requirement extraction agent.
        backend_dev: Code generation agent.
        code_reviewer: Quality gate agent.
        tester: Test generation and execution agent.
        debugger: Root cause analysis and fix loop agent.
        emitter: Optional NATS event emitter for observability.
        shared_state: Graph-level shared state dict flowing between agents.
        workspace_path: Temporary directory for generated code.
    """

    orchestrator: OrchestratorAgent
    backend_dev: BackendDevAgent
    code_reviewer: CodeReviewerAgent
    tester: TesterAgent
    debugger: DebuggerAgent
    emitter: PipelineEventEmitter | None = None
    shared_state: dict[str, Any] = field(default_factory=dict)
    workspace_path: str = ""

    async def run(self, user_input: str) -> dict[str, Any]:
        """Execute the full vertical slice pipeline.

        Phases:
            1. **input_processing** -- OrchestratorAgent extracts requirements
            2. **implementation** -- BackendDevAgent generates code
            3. **quality_assurance** -- CodeReviewerAgent reviews with gate
               (reroutes to implementation on failure, max 2 cycles)
            4. **testing** -- TesterAgent generates and runs tests
            5. **debug_fix** -- DebuggerAgent fixes failures (conditional)

        Args:
            user_input: Natural language project description.

        Returns:
            The final shared_state dict containing all agent outputs.
        """
        self.shared_state["user_input"] = user_input

        if not self.workspace_path:
            self.workspace_path = tempfile.mkdtemp(prefix="codebot-vs-")

        if self.emitter:
            await self.emitter.pipeline_started()

        # --- Phase 1: Input Processing ---
        await self._run_phase(
            phase_name="input_processing",
            agent=self.orchestrator,
            agent_type=AgentType.ORCHESTRATOR,
        )

        # --- Phase 2+3: Implementation + QA loop ---
        for qa_cycle in range(_MAX_QA_REROUTES + 1):
            # Implementation phase
            await self._run_phase(
                phase_name="implementation",
                agent=self.backend_dev,
                agent_type=AgentType.BACKEND_DEV,
            )

            # Quality Assurance phase
            await self._run_phase(
                phase_name="quality_assurance",
                agent=self.code_reviewer,
                agent_type=AgentType.CODE_REVIEWER,
            )

            gate_passed = self.shared_state.get("code_review.gate_passed", False)
            if gate_passed:
                logger.info("Quality gate passed on cycle %d", qa_cycle + 1)
                break

            if qa_cycle < _MAX_QA_REROUTES:
                logger.warning(
                    "Quality gate failed on cycle %d, rerouting to implementation",
                    qa_cycle + 1,
                )
                # Inject review comments for BackendDev to consume
                self.shared_state["review_comments"] = self.shared_state.get(
                    "code_review.comments", []
                )
            else:
                logger.warning(
                    "Quality gate failed after %d reroutes, proceeding to testing",
                    _MAX_QA_REROUTES,
                )

        # --- Phase 4: Testing ---
        await self._run_phase(
            phase_name="testing",
            agent=self.tester,
            agent_type=AgentType.TESTER,
        )

        # --- Phase 5: Debug/Fix (conditional) ---
        tests_passing = self.shared_state.get("tests_passing", False)
        if not tests_passing:
            logger.info("Tests failed, entering debug_fix phase")
            await self._run_phase(
                phase_name="debug_fix",
                agent=self.debugger,
                agent_type=AgentType.DEBUGGER,
            )
        else:
            logger.info("All tests passed, skipping debug_fix phase")

        if self.emitter:
            await self.emitter.pipeline_completed()

        return self.shared_state

    async def _run_phase(
        self,
        phase_name: str,
        agent: OrchestratorAgent
        | BackendDevAgent
        | CodeReviewerAgent
        | TesterAgent
        | DebuggerAgent,
        agent_type: AgentType,
    ) -> AgentOutput:
        """Execute a single pipeline phase with event emission.

        Creates an :class:`AgentInput` from the current shared state,
        runs the agent's ``execute()`` method, merges state updates
        back into shared state, and emits events if an emitter is
        configured.

        Args:
            phase_name: Human-readable phase name for events.
            agent: The agent instance to execute.
            agent_type: The agent's type enum for event metadata.

        Returns:
            The agent's output.

        Raises:
            Exception: Re-raises agent execution errors after emitting
                ``agent_failed`` and ``phase_completed`` events.
        """
        if self.emitter:
            await self.emitter.phase_started(phase_name)

        agent_input = AgentInput(
            task_id=uuid.uuid4(),
            shared_state=self.shared_state,
            context_tiers={"l0": {}, "l1": {}, "l2": {}},
        )

        if self.emitter:
            await self.emitter.agent_started(agent_type, agent.agent_id)

        try:
            output = await agent.execute(agent_input)
        except Exception as exc:
            if self.emitter:
                await self.emitter.agent_failed(agent_type, agent.agent_id, str(exc))
                await self.emitter.phase_completed(phase_name)
            raise

        # Merge agent state_updates into shared_state
        self.shared_state.update(output.state_updates)

        if self.emitter:
            await self.emitter.agent_completed(agent_type, agent.agent_id)
            await self.emitter.phase_completed(phase_name)

        return output


async def build_vertical_slice_graph(
    event_bus: EventBus | None = None,
    pipeline_id: uuid.UUID | None = None,
) -> VerticalSlicePipeline:
    """Build the 5-agent vertical slice pipeline.

    Creates instances of all 5 agents and composes them into a
    :class:`VerticalSlicePipeline`. If an event bus is provided,
    the pipeline will emit NATS events for all agent and phase
    transitions.

    Args:
        event_bus: Optional connected :class:`EventBus` for NATS events.
        pipeline_id: Optional pipeline identifier. Auto-generated if omitted.

    Returns:
        A configured :class:`VerticalSlicePipeline` ready for ``run()``.
    """
    if pipeline_id is None:
        pipeline_id = uuid.uuid4()

    emitter: PipelineEventEmitter | None = None
    if event_bus is not None:
        emitter = PipelineEventEmitter(bus=event_bus, pipeline_id=pipeline_id)

    return VerticalSlicePipeline(
        orchestrator=OrchestratorAgent(),
        backend_dev=BackendDevAgent(),
        code_reviewer=CodeReviewerAgent(),
        tester=TesterAgent(),
        debugger=DebuggerAgent(),
        emitter=emitter,
    )
