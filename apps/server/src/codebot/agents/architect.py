"""ArchitectAgent -- system architecture designer for S3 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract research_output, project_requirements, tech_stack
              from shared_state
- reason(): Build LLM message list with architecture-oriented system prompt
- act(): Return structured architecture output with architecture doc,
         component diagram, data flow, and ADR records
- review(): Validate architecture_doc and component_diagram exist

Covers requirements ARCH-01 through ARCH-05:
  ARCH-01: Component boundary design
  ARCH-02: API surface definition (delegated to APIDesignerAgent)
  ARCH-03: Data model design (delegated to DatabaseDesignerAgent)
  ARCH-04: UI/UX design (delegated to DesignerAgent)
  ARCH-05: Parallel execution of S3 agents with isolated SharedState keys
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
You are the System Architect agent for CodeBot, a multi-agent software
development platform. You operate in the S3 (Architecture & Design) pipeline
stage, after the Research phase. Your purpose is to design the system
architecture, define component boundaries, specify data flows, and author
Architecture Decision Records (ADRs).
</role>

<responsibilities>
- ARCH-01 Component Boundary Design: Decompose the system into well-defined
  components with clear interfaces, ownership, and dependency direction.
  Apply principles of high cohesion and loose coupling. Produce C4 model
  diagrams (Context, Container, Component, Code) showing system structure.
- Data Flow Definition: Map data flows between components including
  synchronous (REST/gRPC) and asynchronous (event bus, message queue)
  communication patterns. Identify data transformation points.
- ADR Authoring: Write Architecture Decision Records for every significant
  technology or design choice. Each ADR must include context, decision,
  consequences, and status (proposed/accepted/deprecated).
- Pattern Selection: Select architectural patterns (microservices, modular
  monolith, event-driven, CQRS, etc.) based on project requirements,
  scale expectations, and team constraints. Justify each choice.
- Cross-Cutting Concerns: Address authentication, authorization, logging,
  monitoring, error handling, and configuration management as architectural
  concerns with consistent strategies across components.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "architecture_doc": comprehensive markdown document describing the system
  architecture, including overview, component descriptions, deployment model,
  and technology justifications
- "component_diagram": C4 model representation as structured JSON with
  components, relationships, and boundaries
- "data_flow": array of data flow objects with source, destination, protocol,
  data_type, and direction fields
- "adr_records": array of ADR objects with id, title, context, decision,
  consequences, and status fields
- "cross_cutting": object describing authentication, logging, monitoring,
  and error handling strategies
</output_format>

<constraints>
- Always produce at least one ADR for the primary architectural pattern choice
- Component diagrams must show all inter-component dependencies
- Data flow definitions must distinguish sync vs async communication
- Address security concerns (auth, authz) as first-class architectural elements
- Do not assume deployment target -- design for portability
- Ensure each component has a single clear owner/team boundary
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.ARCHITECT)
@dataclass(slots=True, kw_only=True)
class ArchitectAgent(BaseAgent):
    """System architecture designer for S3 pipeline stage.

    Designs component boundaries, data flows, ADRs, and cross-cutting
    architectural concerns. Produces C4 model diagrams and comprehensive
    architecture documentation.

    Attributes:
        agent_type: Always ``AgentType.ARCHITECT``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for architecture reasoning).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.ARCHITECT, init=False)
    name: str = "architect"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "diagram_generator",
            "pattern_library",
            "adr_writer",
            "component_designer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for ArchitectAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract architecture context from shared state.

        Pulls research_output, project_requirements, and tech_stack
        from the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with research_output, project_requirements, and tech_stack.
        """
        shared_state = agent_input.shared_state
        return {
            "research_output": shared_state.get("research_output", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
            "tech_stack": shared_state.get("tech_stack", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for architecture design.

        Constructs a message sequence with the system prompt and context
        from the research phase for the architect role.

        Args:
            context: Dict with research_output, project_requirements,
                     tech_stack from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Research output: {context.get('research_output', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}\n\n"
                    f"Tech stack: {context.get('tech_stack', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce architecture output with docs, diagrams, and ADRs.

        In the current implementation, returns a structured placeholder
        that downstream agents (Planner, Designer) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with architecture output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "architecture_doc": "",
                "component_diagram": {},
                "data_flow": [],
                "adr_records": [],
                "cross_cutting": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate architecture output contains required keys.

        Checks that architecture_doc and component_diagram are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            architect_output.
        """
        data = result.data
        review_passed = bool(
            "architecture_doc" in data
            and "component_diagram" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"architect_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Architect agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
