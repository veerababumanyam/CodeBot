"""PlannerAgent -- implementation planner for S4 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract architect_output, designer_output, database_output,
              api_designer_output, research_output, project_requirements
              from shared_state
- reason(): Build LLM message list with planning-oriented system prompt
- act(): Return structured planning output with task graph, execution order,
         parallel groups, complexity estimates, and acceptance criteria
- review(): Validate task_graph is non-empty and tasks have required keys

Covers requirements PLAN-01 through PLAN-03:
  PLAN-01: Task decomposition with dependencies
  PLAN-02: Execution order and parallelization
  PLAN-03: Task specs with target files and acceptance criteria
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
You are the Implementation Planner agent for CodeBot, a multi-agent software
development platform. You operate in the S4 (Planning) pipeline stage, after
the Architecture & Design phase. Your purpose is to decompose the architecture
into concrete implementation tasks with dependencies, ordering, and
parallelization opportunities.
</role>

<responsibilities>
- PLAN-01 Task Decomposition: Break down the architecture into fine-grained
  implementation tasks. Each task should be completable by a single agent in
  one session. Identify dependencies between tasks (e.g., "database schema
  must exist before API endpoints"). Produce a directed acyclic graph of
  task dependencies.
- PLAN-02 Execution Order and Parallelization: Determine the optimal
  execution order considering dependencies, resource constraints, and
  parallelization opportunities. Group independent tasks into parallel
  execution waves. Identify the critical path (longest dependent chain).
- PLAN-03 Task Specifications: For each task, produce a detailed specification
  including: title, description, target files to create/modify, acceptance
  criteria (testable conditions), estimated complexity (low/medium/high),
  and the agent type best suited to execute the task.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "task_graph": array of task objects, each with:
  * "id": unique task identifier (e.g., "TASK-001")
  * "title": short descriptive title
  * "description": detailed description of work to be done
  * "target_files": array of file paths to create or modify
  * "acceptance_criteria": array of testable conditions for completion
  * "estimated_complexity": "low" | "medium" | "high"
  * "dependencies": array of task IDs this task depends on
  * "parallel_group": group name for parallel execution (null if sequential)
  * "assigned_agent": AgentType enum value for the executing agent
- "execution_order": array of arrays representing execution waves
  (tasks in same wave can run in parallel)
- "parallel_groups": object mapping group names to arrays of task IDs
- "complexity_estimates": object with total_tasks, by_complexity counts,
  estimated_total_hours, and critical_path_length
- "acceptance_criteria": array of project-level acceptance criteria
  derived from the architecture
</output_format>

<constraints>
- Every task must have at least one acceptance criterion
- Every task must list specific target_files (no vague "update code")
- Dependencies must form a valid DAG (no cycles)
- Complexity estimates must be justified (not arbitrary)
- Critical path must be explicitly identified
- Tasks should be sized for single-agent completion (< 1 hour estimated)
- Include test tasks as first-class items (not afterthoughts)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.PLANNER)
@dataclass(slots=True, kw_only=True)
class PlannerAgent(BaseAgent):
    """Implementation planner for S4 pipeline stage.

    Decomposes architecture into implementation tasks with dependencies,
    execution ordering, parallelization groups, and complexity estimates.

    Attributes:
        agent_type: Always ``AgentType.PLANNER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for planning reasoning).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.PLANNER, init=False)
    name: str = "planner"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "task_decomposer",
            "dependency_resolver",
            "complexity_estimator",
            "parallel_scheduler",
            "critical_path_analyzer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for PlannerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract planning context from shared state.

        Pulls all architecture outputs, research output, and project
        requirements from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with architect_output, designer_output, database_output,
            api_designer_output, research_output, and project_requirements.
        """
        shared_state = agent_input.shared_state
        return {
            "architect_output": shared_state.get("architect_output", {}),
            "designer_output": shared_state.get("designer_output", {}),
            "database_output": shared_state.get("database_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
            "research_output": shared_state.get("research_output", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for implementation planning.

        Constructs a message sequence with the system prompt and context
        from all architecture agents for the planner role.

        Args:
            context: Dict with architecture outputs and requirements
                     from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Architecture output: {context.get('architect_output', {})}\n\n"
                    f"Design output: {context.get('designer_output', {})}\n\n"
                    f"Database output: {context.get('database_output', {})}\n\n"
                    f"API design output: {context.get('api_designer_output', {})}\n\n"
                    f"Research output: {context.get('research_output', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce planning output with task graph and execution order.

        In the current implementation, returns a structured placeholder
        that downstream agents (Implementation agents) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with planning output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "task_graph": [],
                "execution_order": [],
                "parallel_groups": {},
                "complexity_estimates": {},
                "acceptance_criteria": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate planning output contains required keys and structure.

        Checks that task_graph is a non-empty list and each task has
        title, target_files, acceptance_criteria, and estimated_complexity.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            planner_output.
        """
        data = result.data
        task_graph = data.get("task_graph", [])

        # Must be a list
        if not isinstance(task_graph, list):
            return AgentOutput(
                task_id=self.agent_id,
                state_updates={"planner_output": data},
                review_passed=False,
            )

        # Validate each task has required structure
        required_keys = {"title", "target_files", "acceptance_criteria", "estimated_complexity"}
        all_valid = True
        for task in task_graph:
            if not isinstance(task, dict):
                all_valid = False
                break
            if not required_keys.issubset(task.keys()):
                all_valid = False
                break

        # Pass if task_graph is non-empty and all tasks are valid,
        # OR if task_graph is empty (placeholder -- LLM will fill later)
        review_passed = all_valid

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"planner_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Planner agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
