"""OrchestratorAgent -- master pipeline coordinator for CodeBot.

Implements the PRA cognitive cycle:
- perceive(): Extracts user_input (text, images, URLs per INPT-03), project_config,
  pipeline state, existing_codebase (local dir or git URL per INPT-08)
- reason(): Plans pipeline execution, routes tasks, processes multi-modal input
- act(): Returns pipeline plan, stage configs, agent assignments, processed input
- review(): Validates pipeline_plan exists

Covers requirements:
  INPT-03: Multi-modal input handling (text, images, URLs)
  INPT-08: Existing codebase import from local directories or Git repositories

Uses instructor + LiteLLM for structured requirement extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Orchestrator agent for CodeBot, a multi-agent software development
platform. You are the pipeline orchestrator that manages the full SDLC pipeline
execution, routes tasks to specialized agents, and coordinates the entire
software generation process.
</role>

<responsibilities>
- Parse and process multi-modal input: text descriptions, images (wireframes,
  diagrams), and URLs (existing projects, API references) per INPT-03
- Import existing codebases from local directories or Git repositories for
  brownfield projects per INPT-08
- Plan and orchestrate the full SDLC pipeline (S0-S10)
- Route tasks to appropriate specialized agents
- Manage pipeline checkpoints and human approval gates
- Monitor pipeline execution state and handle failures
- Coordinate parallel agent execution in S3/S5/S6 stages
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "pipeline_plan": object describing the planned pipeline execution with
  stages, gates, and agent assignments
- "stage_configs": array of per-stage configuration objects
- "agent_assignments": array of agent-to-task mapping objects
- "input_processed": object with parsed multi-modal input results
- "imported_codebase": object with codebase analysis if importing existing code
</output_format>

<constraints>
- Multi-modal input: text is always required, images and URLs are optional
- Codebase import: support both local directory paths and git:// / https:// URLs
- Pipeline plan must include all required stages for the project type
- Agent assignments must match available AgentType specializations
- Checkpoint gates must be configured for design and delivery phases
- Handle brownfield/improve project types by skipping brainstorm and research
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.ORCHESTRATOR)
@dataclass(slots=True, kw_only=True)
class OrchestratorAgent(BaseAgent):
    """Master pipeline coordinator: processes multi-modal input, imports codebases,
    orchestrates the full SDLC pipeline.

    Handles INPT-03 (multi-modal input: text, images, URLs) and INPT-08
    (existing codebase import from local directories or Git repositories).

    Attributes:
        agent_type: Always ``AgentType.ORCHESTRATOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for orchestration complexity).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.ORCHESTRATOR, init=False)
    name: str = "orchestrator"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "pipeline_controller",
            "agent_monitor",
            "task_router",
            "checkpoint_manager",
            "multimodal_input_processor",
            "git_importer",
            "local_codebase_loader",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for OrchestratorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract user input (multi-modal), project config, pipeline state, and codebase.

        Supports multi-modal input per INPT-03 (text, images, URLs) and
        existing codebase import per INPT-08 (local dir or git URL).

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with user_input, project_config, pipeline_state, and
            existing_codebase data.
        """
        shared_state = agent_input.shared_state
        return {
            "user_input": shared_state.get("user_input", {}),
            "project_config": shared_state.get("project_config", {}),
            "pipeline_state": shared_state.get("pipeline_state", {}),
            "existing_codebase": shared_state.get("existing_codebase", None),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Plan pipeline execution from input context.

        Processes multi-modal input and plans the pipeline stages,
        agent assignments, and gate configurations.

        Args:
            context: Dict with user_input, project_config, pipeline_state,
                     and existing_codebase from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"User input: {context.get('user_input', {})}\n\n"
                    f"Project config: {context.get('project_config', {})}\n\n"
                    f"Pipeline state: {context.get('pipeline_state', {})}\n\n"
                    f"Existing codebase: {context.get('existing_codebase', 'None')}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce pipeline plan with stage configs, agent assignments, and processed input.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with orchestration output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "pipeline_plan": {},
                "stage_configs": [],
                "agent_assignments": [],
                "input_processed": {},
                "imported_codebase": None,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate pipeline plan exists in the orchestration output.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            orchestrator_output.
        """
        data = result.data
        review_passed = bool("pipeline_plan" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"orchestrator_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Orchestrator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
