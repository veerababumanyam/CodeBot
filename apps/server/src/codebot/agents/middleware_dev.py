"""MiddlewareDevAgent -- middleware/backend developer for S5 Implementation pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract planner_output, architect_output, api_designer_output,
              database_output from shared_state
- reason(): Build LLM message list with middleware development system prompt
- act(): Return structured output with generated files, middleware stack,
         API routes, and auth configuration
- review(): Validate generated_files is a non-empty list

Produces API middleware, authentication layers, request/response pipelines,
and database query layers for the backend service.
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
You are the Middleware Developer agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage,
executing in parallel with other implementation agents in an isolated git
worktree. Your purpose is to generate API middleware, authentication layers,
request/response pipelines, and database query layers that connect the
frontend to backend services.
</role>

<responsibilities>
- API Middleware Generation: Generate middleware components for request
  validation, response serialization, error handling, logging, rate limiting,
  and CORS configuration. Follow FastAPI middleware patterns with proper
  dependency injection.
- Authentication Layers: Implement authentication middleware supporting
  JWT token validation, session management, OAuth2 flows, and API key
  authentication. Generate secure token handling with proper expiry,
  refresh rotation, and revocation support.
- Request/Response Pipelines: Create typed request/response models using
  Pydantic v2 with proper validation, serialization, and error responses.
  Implement pagination, filtering, and sorting patterns for list endpoints.
- Database Query Layers: Generate SQLAlchemy 2.0 async query functions,
  repository patterns, and data access layers. Include proper connection
  pooling, transaction management, and query optimization.
- API Route Definitions: Generate FastAPI route handlers with proper
  type annotations, dependency injection, and OpenAPI documentation.
  Group related endpoints into APIRouter instances.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of objects with "path" and "content" keys
- "middleware_stack": object describing the middleware chain and order
- "api_routes": array of route objects with "path", "method", "handler",
  and "middleware" keys
- "auth_config": object with authentication configuration details
</output_format>

<constraints>
- Use FastAPI dependency injection for middleware composition
- All Pydantic models must use v2 API (model_validate, ConfigDict)
- SQLAlchemy queries must use 2.0-style async session API
- Never store passwords in plain text -- use bcrypt or argon2
- JWT tokens must have configurable expiry and support refresh rotation
- All endpoints must have proper OpenAPI documentation via docstrings
- Use proper HTTP status codes for error responses
- Include rate limiting configuration for public endpoints
- Database operations must use proper transaction boundaries
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.MIDDLEWARE_DEV)
@dataclass(slots=True, kw_only=True)
class MiddlewareDevAgent(BaseAgent):
    """Middleware/backend developer for S5 Implementation pipeline stage.

    Generates API middleware, authentication layers, request/response
    pipelines, and database query layers. Executes in an isolated git
    worktree for parallel safety.

    Attributes:
        agent_type: Always ``AgentType.MIDDLEWARE_DEV``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for code generation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether this agent requires worktree isolation.
    """

    agent_type: AgentType = field(default=AgentType.MIDDLEWARE_DEV, init=False)
    name: str = "middleware_dev"
    model_tier: str = "tier1"
    max_retries: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "file_edit",
            "bash",
            "api_client_generator",
            "auth_middleware",
        ]
    )
    use_worktree: bool = True

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for MiddlewareDevAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract middleware development context from shared state.

        Pulls planner_output, architect_output, api_designer_output,
        and database_output from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planner_output, architect_output, api_designer_output,
            and database_output.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "architect_output": shared_state.get("architect_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
            "database_output": shared_state.get("database_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for middleware code generation.

        Constructs a message sequence with the system prompt and context
        from planning, architecture, and API design phases.

        Args:
            context: Dict with planner_output, architect_output,
                     api_designer_output, database_output from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Planning output (task graph): {context.get('planner_output', {})}\n\n"
                    f"Architecture output: {context.get('architect_output', {})}\n\n"
                    f"API design specification: {context.get('api_designer_output', {})}\n\n"
                    f"Database schema output: {context.get('database_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce middleware code with API routes, auth, and DB layers.

        In the current implementation, returns a structured placeholder
        that downstream agents (CodeReviewer, Tester) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with middleware output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "middleware_stack": {},
                "api_routes": [],
                "auth_config": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate middleware output contains generated files.

        Checks that generated_files is a non-empty list.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            middleware_dev_output.
        """
        data = result.data
        generated_files = data.get("generated_files", [])
        review_passed = bool(
            isinstance(generated_files, list)
            and len(generated_files) > 0
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"middleware_dev_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Middleware Dev agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
