"""OrchestratorAgent -- master coordinator for the vertical slice pipeline.

Implements the PRA cognitive cycle:
- perceive(): Load user input and detect format (natural language, JSON, YAML, Markdown)
- reason(): Extract structured requirements via RequirementExtractor, run ClarificationLoop
- act(): Return requirements for storage in SharedState by AgentNode wrapper
- review(): Validate that functional_requirements is non-empty and all have acceptance criteria

Uses instructor + LiteLLM for structured requirement extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.input.clarifier import ClarificationLoop
from codebot.input.extractor import RequirementExtractor
from codebot.input.models import ExtractedRequirements

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Orchestrator agent for CodeBot, a multi-agent software development
platform. You are the entry point of the pipeline: you receive a user's project
description and coordinate the extraction of structured requirements.
</role>

<responsibilities>
- Parse natural language project descriptions into structured requirements
- Detect input format (plain text, Markdown, JSON, YAML) and adapt extraction
- Identify functional requirements with testable acceptance criteria
- Flag ambiguities and low-confidence extractions for clarification
- Assign MoSCoW priorities and confidence scores to each requirement
- Coordinate the downstream pipeline phases (implementation, QA, testing, debug)
</responsibilities>

<output_format>
Produce an ExtractedRequirements object containing:
- project_name and project_description
- functional_requirements with id, title, description, priority, acceptance_criteria, confidence
- non_functional_requirements as string descriptions
- constraints as string descriptions
- ambiguities listing any unclear items
</output_format>

<constraints>
- Every functional requirement MUST have at least one acceptance criterion
- Confidence scores MUST be between 0.0 and 1.0
- Priority MUST be one of: Must, Should, Could, Won't (MoSCoW)
- Requirement IDs MUST follow the pattern FR-XX (e.g. FR-01, FR-02)
- Flag ambiguities honestly -- do not fabricate certainty
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class OrchestratorAgent(BaseAgent):
    """Master coordinator: parses input, extracts requirements, orchestrates pipeline.

    Wraps the RequirementExtractor and ClarificationLoop in the PRA
    cognitive cycle pattern from BaseAgent.

    Attributes:
        agent_type: Always ``AgentType.ORCHESTRATOR``.
        model: LiteLLM model identifier for requirement extraction.
        confidence_threshold: Minimum confidence for ClarificationLoop.
    """

    agent_type: AgentType = field(default=AgentType.ORCHESTRATOR, init=False)
    model: str = "anthropic/claude-sonnet-4"
    confidence_threshold: float = 0.7

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for Orchestrator.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Load user input and detect format.

        Args:
            agent_input: The task input with shared_state containing user_input.

        Returns:
            Dict with user_input string and detected input_format.
        """
        user_input = agent_input.shared_state.get("user_input", "")
        input_format = RequirementExtractor._detect_format(user_input)
        return {"user_input": user_input, "input_format": input_format}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract structured requirements from input.

        Creates a RequirementExtractor, calls extract(), and runs the
        ClarificationLoop to detect ambiguities and low-confidence items.

        Args:
            context: Dict with user_input and input_format from perceive().

        Returns:
            Dict with requirements (ExtractedRequirements), needs_clarification
            flag, and clarification_items list.
        """
        extractor = RequirementExtractor(model=self.model)
        requirements = await extractor.extract(context["user_input"])

        clarifier = ClarificationLoop(confidence_threshold=self.confidence_threshold)
        clarification_items = clarifier.check(requirements)

        return {
            "requirements": requirements,
            "needs_clarification": clarifier.needs_clarification,
            "clarification_items": clarification_items,
        }

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Store requirements for downstream agents.

        In the vertical slice, ambiguities are logged but the pipeline
        proceeds with best-effort extraction.  Full human-in-the-loop
        clarification is deferred to Phase 9.

        Args:
            plan: Dict with requirements and needs_clarification from reason().

        Returns:
            PRAResult with is_complete=True and requirements in data.
        """
        requirements: ExtractedRequirements = plan["requirements"]

        if plan.get("needs_clarification") and requirements.ambiguities:
            logger.warning(
                "Ambiguities detected but proceeding with best-effort extraction: %s",
                requirements.ambiguities,
            )

        return PRAResult(
            is_complete=True,
            data={"requirements": requirements},
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Verify extracted requirements are non-empty and well-formed.

        Checks that at least one functional requirement was extracted and
        that all functional requirements have acceptance criteria.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed indicating acceptance.
        """
        requirements: ExtractedRequirements = result.data["requirements"]
        review_passed = (
            len(requirements.functional_requirements) > 0
            and all(
                fr.acceptance_criteria
                for fr in requirements.functional_requirements
            )
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"requirements": requirements.model_dump()},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Orchestrator agent.

        Returns:
            The SYSTEM_PROMPT constant with role, responsibilities,
            output format, and constraints.
        """
        return SYSTEM_PROMPT
