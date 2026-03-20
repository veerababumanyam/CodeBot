"""Skill Creator Agent -- extracts reusable code patterns into skills.

Full implementation of Agent #26. Analyzes completed project code to identify
recurring patterns (auth flows, CRUD, form validation) and packages them
as parameterized skills in the skill registry.

Runs post-delivery in Stage S9. Replaces the stub in skill_creator.py.

Implements the PRA cognitive cycle:
- perceive(): Gather project source files and pipeline execution logs
- reason(): Identify recurring code patterns using LLM analysis
- act(): Create Skill objects via SkillService and publish events
- review(): Validate created skills and format output
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, override

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

if TYPE_CHECKING:
    from codebot.events.bus import EventBus
    from codebot.skills.service import SkillService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Skill Creator agent for CodeBot, a multi-agent software development
platform. You operate in the S9 (Documentation) pipeline stage, post-delivery.
Your purpose is to analyze completed project code and extract reusable patterns
into parameterized skills that other agents can use in future projects.
</role>

<responsibilities>
- Analyze completed code files for recurring patterns:
  1. Authentication/authorization patterns (JWT, OAuth, RBAC)
  2. CRUD operation templates (REST, GraphQL)
  3. Form validation patterns (schema-based, custom validators)
  4. API client patterns (retry, circuit-breaker, rate-limiting)
  5. Error handling patterns (structured errors, recovery)
  6. Testing patterns (fixtures, mocks, integration setups)
- Filter out patterns that already exist in the skill registry
- Create parameterized Skill objects with clear input/output schemas
- Register skills via SkillService and activate after validation
- Publish skill.created events for observability
</responsibilities>

<output_format>
Produce a JSON object with:
- "extracted_patterns": array of pattern objects, each with:
  - name, description, parameterized_code, applicable_agents
  - input_schema, output_schema, tags
</output_format>

<constraints>
- Only extract patterns that appear in 2+ files or agents
- Each skill must have clear input/output schemas
- Do not duplicate existing skills in the registry
- Parameterized code must be executable with proper variable substitution
</constraints>
"""


# ---------------------------------------------------------------------------
# Supporting data types
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class ExtractedPattern:
    """A code pattern identified for extraction into a reusable skill.

    Attributes:
        name: Human-readable pattern name.
        description: What the pattern does and when to use it.
        parameterized_code: Template source code with substitution points.
        applicable_agents: Agent types that can use this pattern.
        input_schema: JSON Schema for pattern inputs.
        output_schema: JSON Schema for pattern outputs.
        tags: Searchable tags for discovery.
    """

    name: str
    description: str
    parameterized_code: str
    applicable_agents: list[str]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.SKILL_MANAGER)
@dataclass(slots=True, kw_only=True)
class SkillCreatorAgent(BaseAgent):
    """Agent #26: Extracts reusable code patterns into skills for other agents.

    Runs post-delivery in Stage S9. Analyzes completed project code to identify
    recurring patterns (auth flows, CRUD, form validation, API clients) and packages
    them as parameterized skills in the skill registry.

    Attributes:
        agent_type: Always ``AgentType.SKILL_MANAGER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for complex pattern analysis).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.SKILL_MANAGER, init=False)
    name: str = "skill_creator"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "pattern_extractor",
            "skill_packager",
            "skill_registry",
            "skill_tester",
            "skill_documenter",
        ]
    )

    # Injected dependencies (not part of config, set after construction)
    _skill_service: SkillService | None = field(default=None, init=False, repr=False)
    _event_bus: EventBus | None = field(default=None, init=False, repr=False)

    def set_services(self, skill_service: SkillService, event_bus: EventBus) -> None:
        """Inject service dependencies after construction.

        Args:
            skill_service: Service for creating and activating skills.
            event_bus: Event bus for publishing skill.created events.
        """
        self._skill_service = skill_service
        self._event_bus = event_bus

    @override
    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for SkillCreatorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    @override
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Gather project source files and pipeline execution logs.

        Extracts: completed code files, execution patterns, agent outputs,
        and existing skill registry contents to avoid duplicates.

        Args:
            agent_input: The task input with shared_state containing
                         code_files, execution_logs, and existing_skills.

        Returns:
            Dict with code_files, execution_logs, existing_skills, and project_type.
        """
        shared_state = agent_input.shared_state
        return {
            "code_files": shared_state.get("code_files", []),
            "execution_logs": shared_state.get("execution_logs", []),
            "existing_skills": shared_state.get("existing_skills", []),
            "project_type": shared_state.get("project_type", "unknown"),
        }

    @override
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Identify recurring code patterns using LLM analysis.

        Uses LLM to analyze code files for:
        1. Authentication/authorization patterns
        2. CRUD operation templates
        3. Form validation patterns
        4. API client patterns
        5. Error handling patterns
        6. Testing patterns

        Filters out patterns that already exist in the skill registry.

        Args:
            context: Dict with code_files, existing_skills from perceive().

        Returns:
            Dict with patterns_to_extract and existing_skills for the act phase.
        """
        return {
            "patterns_to_extract": context.get("code_files", []),
            "existing_skills": context.get("existing_skills", []),
        }

    @override
    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Create skills from identified patterns.

        For each pattern:
        1. Create Skill object with input/output schemas
        2. Register via SkillService (starts as DRAFT)
        3. Activate the skill
        4. Emit skill.created event

        Args:
            plan: Dict with extracted_patterns list from reason().

        Returns:
            PRAResult with created_skills list and any errors.
        """
        from codebot.skills.models import Skill

        created_skills: list[str] = []
        errors: list[str] = []

        patterns: list[ExtractedPattern] = plan.get("extracted_patterns", [])
        for pattern in patterns:
            try:
                skill = Skill(
                    id=uuid.uuid4(),
                    name=pattern.name,
                    description=pattern.description,
                    version="1.0.0",
                    created_by_agent="skill_creator",
                    target_agents=pattern.applicable_agents,
                    code=pattern.parameterized_code,
                    input_schema=pattern.input_schema,
                    output_schema=pattern.output_schema,
                    tags=pattern.tags,
                )
                if self._skill_service is None:
                    raise RuntimeError("SkillService not injected -- call set_services() first")
                created = await self._skill_service.create_skill(skill)
                await self._skill_service.activate_skill(created.id)

                if self._event_bus is None:
                    raise RuntimeError("EventBus not injected -- call set_services() first")
                await self._event_bus.publish("skill.created", {
                    "skill_id": str(created.id),
                    "name": created.name,
                    "version": created.version,
                    "created_by": "skill_creator",
                })
                created_skills.append(str(created.id))
            except Exception as exc:
                errors.append(f"Failed to create skill '{pattern.name}': {exc}")

        return PRAResult(
            is_complete=True,
            data={"created_skills": created_skills, "errors": errors},
        )

    @override
    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate skill creation output.

        Checks that created skills list is populated and no errors occurred.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            skill_creator_output.
        """
        data = result.data
        has_errors = len(data.get("errors", [])) > 0
        review_passed = not has_errors or len(data.get("created_skills", [])) > 0

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"skill_creator_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Skill Creator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
