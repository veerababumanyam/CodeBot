"""DocumentationWriterAgent -- S9 Documentation pipeline stage agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts all *_output keys, architect_output (ADRs), api_designer_output
  (API docs), infra_engineer_output (deployment guides) from shared_state
- reason(): Builds LLM message list with documentation-oriented system prompt
- act(): Returns structured documentation output with API docs, user guide, ADRs,
  deployment guide
- review(): Validates api_docs and user_guide exist

Covers requirements:
  DOCS-01: Generates API docs from code (OpenAPI rendering)
  DOCS-02: Creates user guides and setup instructions
  DOCS-03: Produces Architecture Decision Records (ADRs)
  DOCS-04: Includes deployment guides from infrastructure config
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
You are the Documentation Writer agent for CodeBot, a multi-agent software
development platform. You operate in the S9 (Documentation) pipeline stage.
Your purpose is to produce comprehensive, accurate documentation for the
generated project.
</role>

<responsibilities>
- DOCS-01 API Documentation: Generate API reference documentation from code,
  including OpenAPI/Swagger rendering, endpoint descriptions, request/response
  schemas, authentication requirements, and error codes.
- DOCS-02 User Guides: Create user guides and setup instructions covering
  installation, configuration, getting started, and common workflows.
- DOCS-03 Architecture Decision Records (ADRs): Produce ADR documents from
  architectural decisions made during the design phase, following the standard
  ADR format (Title, Status, Context, Decision, Consequences).
- DOCS-04 Deployment Guides: Generate deployment documentation from
  infrastructure configuration, covering Docker, Kubernetes, CI/CD pipeline
  setup, environment variables, and monitoring.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "api_docs": object with endpoint documentation, schema references, and
  OpenAPI spec sections
- "user_guide": object with installation, configuration, getting_started,
  and workflows sections
- "setup_instructions": step-by-step setup guide as a string or structured object
- "adr_records": array of ADR objects, each with title, status, context,
  decision, and consequences
- "deployment_guide": object with docker, kubernetes, ci_cd, env_vars, and
  monitoring sections
- "generated_files": array of file path strings for all generated documentation
</output_format>

<constraints>
- API docs MUST reference actual endpoint paths and HTTP methods
- ADRs MUST follow the standard ADR template format
- Deployment guides MUST include environment variable documentation
- User guides MUST include a "Getting Started" section
- All documentation MUST be written in clear, concise Markdown
- Do NOT invent features or endpoints not present in the codebase
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.DOC_WRITER)
@dataclass(slots=True, kw_only=True)
class DocumentationWriterAgent(BaseAgent):
    """S9 documentation generation agent for API docs, guides, ADRs, and deployment docs.

    Consumes outputs from all upstream agents to produce comprehensive project
    documentation covering API references, user guides, architecture decision
    records, and deployment instructions.

    Attributes:
        agent_type: Always ``AgentType.DOC_WRITER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.DOC_WRITER, init=False)
    name: str = "doc_writer"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "openapi_renderer",
            "docstring_generator",
            "readme_generator",
            "diagram_renderer",
            "adr_formatter",
            "deployment_guide_generator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for DocumentationWriterAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract all output keys and documentation-relevant context from shared state.

        Pulls all ``*_output`` keys, plus specifically ``architect_output`` (for ADRs),
        ``api_designer_output`` (for API docs), and ``infra_engineer_output``
        (for deployment guides).

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with all_outputs, architect_output, api_designer_output,
            and infra_engineer_output.
        """
        shared_state = agent_input.shared_state
        all_outputs: dict[str, Any] = {}
        for key, value in shared_state.items():
            if key.endswith("_output"):
                all_outputs[key] = value

        return {
            "all_outputs": all_outputs,
            "architect_output": shared_state.get("architect_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
            "infra_engineer_output": shared_state.get("infra_engineer_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for documentation generation.

        Constructs a message sequence with the system prompt and all
        upstream agent outputs for comprehensive documentation generation.

        Args:
            context: Dict with all_outputs and specific output keys from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"All agent outputs: {context.get('all_outputs', {})}\n\n"
                    f"Architect output (for ADRs): {context.get('architect_output', {})}\n\n"
                    f"API designer output (for API docs): {context.get('api_designer_output', {})}\n\n"
                    f"Infra engineer output (for deployment guide): "
                    f"{context.get('infra_engineer_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce documentation output with API docs, user guide, ADRs, and deployment guide.

        In the current implementation, returns a structured placeholder
        that can be consumed by downstream systems. The actual LLM call
        is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with documentation output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "api_docs": {},
                "user_guide": {},
                "setup_instructions": "",
                "adr_records": [],
                "deployment_guide": {},
                "generated_files": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate documentation output contains required sections.

        Checks that api_docs and user_guide are present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            doc_writer_output.
        """
        data = result.data
        review_passed = bool("api_docs" in data and "user_guide" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"doc_writer_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Documentation Writer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
