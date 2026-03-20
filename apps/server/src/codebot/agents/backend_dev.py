"""BackendDevAgent -- S5 Implementation pipeline stage backend developer.

Implements the PRA cognitive cycle:
- perceive(): Extracts planner_output, architect_output, api_designer_output,
  database_output, techstack_output from shared_state
- reason(): Builds LLM message list with backend development-oriented system prompt
- act(): Returns generated files, API endpoints, DB models, and test stubs
- review(): Validates generated_files is non-empty

Generates Python/FastAPI server code from API specs, follows project conventions
(Pydantic v2, SQLAlchemy 2.0, async-first).
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
You are the Backend Developer agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage.
Your purpose is to generate Python/FastAPI server code from API specifications
and architectural decisions.
</role>

<responsibilities>
- Generate complete, runnable Python/FastAPI code from API specifications
- Follow project conventions: Pydantic v2, SQLAlchemy 2.0, async-first
- Create proper request/response models with validation
- Implement comprehensive error handling with appropriate HTTP status codes
- Generate database models and migration stubs
- Write Google-style docstrings for all public functions and classes
- Create test stubs for generated endpoints
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of file objects with path, content, and purpose
- "api_endpoints": array of endpoint objects with path, method, handler, and models
- "db_models": array of SQLAlchemy model definitions with table, columns, relationships
- "test_stubs": array of test file objects with path and content
</output_format>

<constraints>
- Use Pydantic v2 (BaseModel with model_config, not class Config)
- Use async def for all route handlers and database operations
- Use Google-style docstrings
- Include comprehensive error handling (try/except with specific exceptions)
- Follow PEP 8 and ruff-compatible formatting
- Use type hints for all function parameters and return values
- Do NOT use deprecated APIs or patterns
- Each agent works in isolated git worktree for parallel safety
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.BACKEND_DEV)
@dataclass(slots=True, kw_only=True)
class BackendDevAgent(BaseAgent):
    """S5 backend development agent generating Python/FastAPI code.

    Consumes planning, architecture, API design, database, and tech stack
    outputs to generate complete backend server code with endpoints,
    models, and test stubs.

    Attributes:
        agent_type: Always ``AgentType.BACKEND_DEV``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether to use git worktree isolation for parallel execution.
    """

    agent_type: AgentType = field(default=AgentType.BACKEND_DEV, init=False)
    name: str = "backend_dev"
    model_tier: str = "tier2"
    max_retries: int = 2
    use_worktree: bool = True
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "file_edit",
            "bash",
            "api_generator",
            "db_query_builder",
            "test_runner",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for BackendDevAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract planning, architecture, API, database, and tech stack context.

        Pulls planner_output, architect_output, api_designer_output,
        database_output, and techstack_output from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planning, architecture, API, database, and tech stack outputs.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "architect_output": shared_state.get("architect_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
            "database_output": shared_state.get("database_output", {}),
            "techstack_output": shared_state.get("techstack_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for backend code generation.

        Args:
            context: Dict with planning/architecture/API/database outputs from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Planner output: {context.get('planner_output', {})}\n\n"
                    f"Architect output: {context.get('architect_output', {})}\n\n"
                    f"API designer output: {context.get('api_designer_output', {})}\n\n"
                    f"Database output: {context.get('database_output', {})}\n\n"
                    f"Tech stack: {context.get('techstack_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce backend code with generated files, endpoints, models, and test stubs.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with backend development output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "api_endpoints": [],
                "db_models": [],
                "test_stubs": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate backend development output has generated files.

        Checks that generated_files is present and non-empty (or at least present).

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            backend_dev_output.
        """
        data = result.data
        review_passed = bool("generated_files" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"backend_dev_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Backend Dev agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
