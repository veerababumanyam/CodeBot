"""ResearcherAgent -- technical researcher for S2 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract brainstorming_output, tech_stack_preferences,
              project_requirements from shared_state
- reason(): Build LLM message list with research-oriented system prompt
- act(): Return structured research output with library evaluations,
         best practices, risk assessment, and research report
- review(): Validate library_evaluations and research_report exist

Covers requirements RSRC-01 through RSRC-04:
  RSRC-01: Library/API/framework evaluation
  RSRC-02: Best practices discovery
  RSRC-03: Risk identification
  RSRC-04: Structured context for Architecture phase
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
You are the Researcher agent for CodeBot, a multi-agent software development
platform. You operate in the S2 (Research) pipeline stage, after the
Brainstorming phase. Your purpose is to investigate technologies, evaluate
dependencies, discover best practices, and produce structured research
findings that inform the Architecture and Design phases.
</role>

<responsibilities>
- RSRC-01 Library and Framework Evaluation: Investigate frameworks, libraries,
  and APIs identified in the brainstorming output. For each candidate, evaluate
  maintenance status (last commit, open issues, release frequency), community
  health (GitHub stars, npm/PyPI downloads), documentation quality, and known
  security vulnerabilities. Always evaluate at least 2 alternatives per library
  choice. Produce a structured evaluation with name, pros, cons, and a
  normalized score (0.0-1.0).
- RSRC-02 Best Practices Discovery: Identify design patterns, architectural
  patterns, and implementation best practices applicable to the project
  requirements. Search for reference implementations and open-source projects
  with similar architectures. Document findings with citations and code examples.
- RSRC-03 Risk Identification: Assess technical risks including dependency
  health, licensing implications (especially GPL/AGPL), known CVEs in
  dependency trees, API stability and deprecation risks, and scalability
  limitations. Always check for known CVEs before recommending any dependency.
- RSRC-04 Structured Context for Architecture: Package research findings into
  a structured format consumable by the Architect agent, including technology
  recommendations with confidence scores, pattern recommendations, and a
  comprehensive research report with executive summary.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "library_evaluations": array of objects, each with "name", "category",
  "pros" (array), "cons" (array), "score" (0.0-1.0), "license",
  "last_updated", "known_cves" (array)
- "best_practices": array of objects with "pattern", "description",
  "applicability", "references" (array of URLs)
- "risk_assessment": array of objects with "description", "category"
  (dependency|licensing|security|scalability), "likelihood" (low|medium|high),
  "impact" (low|medium|high), "mitigation"
- "compatibility_analysis": object with "compatible_pairs" and
  "conflict_pairs" describing inter-library compatibility
- "research_report": string containing a comprehensive markdown report
  summarizing all findings with an executive summary
</output_format>

<constraints>
- Always evaluate at least 2 alternatives per library category
- Always check for known CVEs before recommending a dependency
- Include license information for every evaluated library
- Score libraries on a 0.0-1.0 scale using consistent criteria
- Cite sources: include URLs for claims about maintenance, security, or best practices
- Flag GPL/AGPL dependencies that may affect project licensing
- Do not recommend deprecated or unmaintained libraries (no commit in 12+ months)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.RESEARCHER)
@dataclass(slots=True, kw_only=True)
class ResearcherAgent(BaseAgent):
    """Technical researcher for S2 pipeline stage.

    Investigates libraries, evaluates dependencies, discovers best practices,
    identifies risks, and produces structured research output for the
    Architecture phase.

    Attributes:
        agent_type: Always ``AgentType.RESEARCHER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for research reasoning).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.RESEARCHER, init=False)
    name: str = "researcher"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "web_search",
            "github_search",
            "package_registry",
            "docs_reader",
            "reference_finder",
            "dependency_analyzer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for ResearcherAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract research context from shared state.

        Pulls brainstorming_output, tech_stack_preferences, and
        project_requirements from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with brainstorming_output, tech_stack_preferences,
            and project_requirements.
        """
        shared_state = agent_input.shared_state
        return {
            "brainstorming_output": shared_state.get("brainstorming_output", {}),
            "tech_stack_preferences": shared_state.get("tech_stack_preferences", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for research.

        Constructs a message sequence with the system prompt and context
        from the brainstorming phase for the researcher role.

        Args:
            context: Dict with brainstorming_output, tech_stack_preferences,
                     project_requirements from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Brainstorming output: {context.get('brainstorming_output', {})}\n\n"
                    f"Tech stack preferences: {context.get('tech_stack_preferences', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce research output with library evaluations and report.

        In the current implementation, returns a structured placeholder
        that downstream agents (Architect, Designer) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with research output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "library_evaluations": [],
                "best_practices": [],
                "risk_assessment": [],
                "compatibility_analysis": {},
                "research_report": "",
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate research output contains required keys.

        Checks that library_evaluations and research_report are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            research_output.
        """
        data = result.data
        review_passed = bool(
            "library_evaluations" in data
            and "research_report" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"research_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Researcher agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
