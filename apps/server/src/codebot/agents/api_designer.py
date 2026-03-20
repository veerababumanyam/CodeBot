"""APIDesignerAgent -- API specification designer for S3 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract architect_output, database_output, project_requirements
              from shared_state
- reason(): Build LLM message list with API design system prompt
- act(): Return structured API output with spec, endpoint definitions,
         auth scheme, and rate limiting
- review(): Validate api_spec and endpoint_definitions exist

Covers requirement ARCH-02:
  ARCH-02: REST/GraphQL API specification generation
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
You are the API Designer agent for CodeBot, a multi-agent software
development platform. You operate in the S3 (Architecture & Design) pipeline
stage. Your purpose is to design REST and/or GraphQL API specifications,
define endpoints, authentication schemes, and rate limiting policies.
</role>

<responsibilities>
- ARCH-02 API Specification: Generate comprehensive API specifications in
  OpenAPI 3.1 format for REST APIs and/or GraphQL schema definition language.
  Include request/response schemas, error responses, and examples.
- Endpoint Design: Define all API endpoints with HTTP methods, URL paths,
  query parameters, request bodies, and response schemas. Follow RESTful
  conventions (resource-oriented URLs, proper HTTP status codes, HATEOAS
  links where appropriate).
- Authentication Scheme: Design the API authentication strategy including
  JWT token flow, OAuth2 scopes, API key management, and session handling.
  Define which endpoints require authentication and authorization levels.
- Rate Limiting: Define rate limiting policies per endpoint or endpoint
  group, including burst limits, sustained limits, and rate limit headers
  (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).
- Versioning Strategy: Define the API versioning approach (URL path, header,
  or query parameter) and deprecation policy for breaking changes.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "api_spec": OpenAPI 3.1 specification as a structured JSON object
  with paths, components/schemas, and security schemes
- "endpoint_definitions": array of endpoint objects with method, path,
  description, request_schema, response_schema, auth_required,
  and rate_limit fields
- "auth_scheme": object describing authentication strategy with type
  (jwt|oauth2|apikey), token_flow, scopes, and refresh_policy
- "rate_limiting": object with default_limits, per_endpoint_overrides,
  and headers configuration
- "versioning": object with strategy, current_version, and
  deprecation_policy fields
</output_format>

<constraints>
- All endpoints must have documented request and response schemas
- Error responses must follow RFC 7807 (Problem Details for HTTP APIs)
- Authentication must support token refresh without full re-authentication
- Rate limits must be configurable per API consumer tier
- API must be backwards-compatible within a major version
- Include pagination for all list endpoints (cursor-based preferred)
- Include CORS configuration recommendations
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.API_DESIGNER)
@dataclass(slots=True, kw_only=True)
class APIDesignerAgent(BaseAgent):
    """API specification designer for S3 pipeline stage.

    Designs REST/GraphQL API specifications, defines endpoints,
    authentication schemes, rate limiting, and versioning strategies.

    Attributes:
        agent_type: Always ``AgentType.API_DESIGNER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for API design reasoning).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.API_DESIGNER, init=False)
    name: str = "api_designer"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "openapi_designer",
            "graphql_designer",
            "api_validator",
            "endpoint_generator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for APIDesignerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract API design context from shared state.

        Pulls architect_output, database_output, and project_requirements
        from the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with architect_output, database_output, and
            project_requirements.
        """
        shared_state = agent_input.shared_state
        return {
            "architect_output": shared_state.get("architect_output", {}),
            "database_output": shared_state.get("database_output", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for API design.

        Constructs a message sequence with the system prompt and context
        from the architecture phase for the API designer role.

        Args:
            context: Dict with architect_output, database_output,
                     project_requirements from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Architecture output: {context.get('architect_output', {})}\n\n"
                    f"Database output: {context.get('database_output', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce API design output with spec and endpoints.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual LLM call is handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with API design output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "api_spec": {},
                "endpoint_definitions": [],
                "auth_scheme": {},
                "rate_limiting": {},
                "versioning": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate API output contains required keys.

        Checks that api_spec and endpoint_definitions are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            api_designer_output.
        """
        data = result.data
        review_passed = bool(
            "api_spec" in data
            and "endpoint_definitions" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"api_designer_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the API Designer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
