"""IntegrationsAgent -- integrations adapter for S5 Implementation pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract planner_output, architect_output, api_designer_output
              from shared_state
- reason(): Build LLM message list with integrations system prompt
- act(): Return structured output with generated files, API clients,
         webhook handlers, and SDK wrappers
- review(): Validate generated_files is a non-empty list

Generates third-party API client code, webhook handlers, and SDK wrappers
for external service integrations.
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
You are the Integrations Adapter agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage,
executing in parallel with other implementation agents in an isolated git
worktree. Your purpose is to generate third-party API client code, webhook
handlers, and SDK wrappers for external service integrations.
</role>

<responsibilities>
- API Client Generation: Generate typed HTTP client wrappers for third-party
  APIs identified in the architecture output. Use httpx for async HTTP
  clients with proper retry logic, timeout configuration, and error handling.
  Generate Pydantic v2 models for API request/response payloads.
- Webhook Handlers: Create webhook receiver endpoints with proper signature
  verification, idempotency handling, and event routing. Support common
  webhook patterns (Stripe, GitHub, Twilio, SendGrid).
- SDK Wrappers: Generate thin wrapper layers around third-party SDKs to
  provide a consistent interface, error normalization, and telemetry.
  Abstract vendor-specific patterns behind clean interfaces.
- Authentication Adapters: Generate OAuth2 client credential flows, API key
  management, and token refresh logic for third-party service authentication.
- Rate Limit Handling: Implement client-side rate limiting with exponential
  backoff, retry-after header parsing, and request queuing for APIs with
  strict rate limits.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of objects with "path" and "content" keys
- "api_clients": array of API client objects with "service", "base_url",
  "endpoints", and "auth_type" keys
- "webhook_handlers": array of webhook handler objects with "service",
  "event_types", and "verification_method" keys
- "sdk_wrappers": array of SDK wrapper objects with "service", "sdk_package",
  and "wrapped_methods" keys
</output_format>

<constraints>
- Use httpx for all async HTTP clients (not requests or aiohttp)
- All API clients must support configurable timeouts and retry policies
- Webhook handlers must verify signatures before processing events
- Never store API keys or secrets in source code -- use environment variables
- All third-party interactions must be logged for observability
- Generate typed response models using Pydantic v2
- Include proper error mapping from vendor errors to application errors
- SDK wrappers must not leak vendor-specific exceptions
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.INTEGRATION_ADAPTER)
@dataclass(slots=True, kw_only=True)
class IntegrationsAgent(BaseAgent):
    """Integrations adapter for S5 Implementation pipeline stage.

    Generates third-party API client code, webhook handlers, and SDK
    wrappers for external service integrations. Executes in an isolated
    git worktree for parallel safety.

    Attributes:
        agent_type: Always ``AgentType.INTEGRATION_ADAPTER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for code generation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether this agent requires worktree isolation.
    """

    agent_type: AgentType = field(default=AgentType.INTEGRATION_ADAPTER, init=False)
    name: str = "integrations"
    model_tier: str = "tier1"
    max_retries: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "bash",
            "api_client_generator",
            "sdk_wrapper",
        ]
    )
    use_worktree: bool = True

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for IntegrationsAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract integrations context from shared state.

        Pulls planner_output, architect_output, and api_designer_output
        from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planner_output, architect_output, and
            api_designer_output.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "architect_output": shared_state.get("architect_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for integration code generation.

        Constructs a message sequence with the system prompt and context
        from planning, architecture, and API design phases.

        Args:
            context: Dict with planner_output, architect_output,
                     api_designer_output from perceive().

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
                    f"API design specification: {context.get('api_designer_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce integration code with API clients, webhooks, and wrappers.

        In the current implementation, returns a structured placeholder
        that downstream agents (CodeReviewer, Tester) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with integration output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "api_clients": [],
                "webhook_handlers": [],
                "sdk_wrappers": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate integration output contains generated files.

        Checks that generated_files is a non-empty list.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            integrations_output.
        """
        data = result.data
        generated_files = data.get("generated_files", [])
        review_passed = bool(
            isinstance(generated_files, list)
            and len(generated_files) > 0
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"integrations_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Integrations agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
