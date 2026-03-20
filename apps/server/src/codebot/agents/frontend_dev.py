"""FrontendDevAgent -- frontend developer for S5 Implementation pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract planner_output, designer_output, template_output,
              techstack_output from shared_state
- reason(): Build LLM message list with frontend development system prompt
- act(): Return structured output with generated files, component tree,
         route definitions, and test stubs
- review(): Validate generated_files is a non-empty list with path+content entries

Covers requirement IMPL-01: Frontend code generation.
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
You are the Frontend Developer agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage,
executing in parallel with other implementation agents in an isolated git
worktree. Your purpose is to generate production-quality React/TypeScript UI
code from design specifications and planning outputs.
</role>

<responsibilities>
- IMPL-01 Frontend Code Generation: Generate React/TypeScript UI code from
  design specs including components, pages, layouts, and shared UI primitives.
  Follow project conventions: ESM modules, Tailwind CSS for styling, Zustand
  for client state, TanStack Query for server state and data fetching.
- Component Architecture: Create a well-structured component tree matching
  the designer's wireframes and component hierarchy. Use composition patterns,
  separate presentational and container components.
- Route Definitions: Generate route configurations matching the navigation
  structure from the design phase. Use file-based routing conventions where
  applicable (Next.js, Remix) or explicit route definitions (React Router).
- State Management: Set up Zustand stores for client-side state and TanStack
  Query hooks for server data. Ensure proper cache invalidation patterns.
- Test Stubs: Generate test stub files for each component using Vitest and
  React Testing Library conventions.
- Accessibility: Follow WAI-ARIA best practices, use semantic HTML, ensure
  keyboard navigation support, and include proper alt text for images.
- Responsive Design: Implement mobile-first responsive layouts using Tailwind
  breakpoint utilities.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of objects with "path" and "content" keys
- "component_tree": hierarchical object describing the component structure
- "route_definitions": array of route objects with "path", "component",
  and "layout" keys
- "test_stubs": array of test file objects with "path" and "content" keys
</output_format>

<constraints>
- All generated files must use ESM imports (no CommonJS require)
- Use TypeScript strict mode throughout
- Style with Tailwind CSS utilities -- no custom CSS unless unavoidable
- Use Zustand for client state, TanStack Query for server state
- Generate one component per file following lowercase-hyphen naming convention
- Include proper TypeScript types and interfaces for all props
- Do not hardcode API endpoints -- use environment variables or config
- Follow the project's component naming conventions from techstack_output
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.FRONTEND_DEV)
@dataclass(slots=True, kw_only=True)
class FrontendDevAgent(BaseAgent):
    """Frontend developer for S5 Implementation pipeline stage.

    Generates React/TypeScript UI code from design specifications,
    including components, routes, state management, and test stubs.
    Executes in an isolated git worktree for parallel safety.

    Attributes:
        agent_type: Always ``AgentType.FRONTEND_DEV``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for code generation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether this agent requires worktree isolation.
    """

    agent_type: AgentType = field(default=AgentType.FRONTEND_DEV, init=False)
    name: str = "frontend_dev"
    model_tier: str = "tier1"
    max_retries: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "file_edit",
            "bash",
            "browser_preview",
            "component_generator",
            "style_generator",
        ]
    )
    use_worktree: bool = True

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for FrontendDevAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract frontend development context from shared state.

        Pulls planner_output (task graph), designer_output (wireframes and
        component hierarchy), template_output (scaffold), and techstack_output
        from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planner_output, designer_output, template_output,
            and techstack_output.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "designer_output": shared_state.get("designer_output", {}),
            "template_output": shared_state.get("template_output", {}),
            "techstack_output": shared_state.get("techstack_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for frontend code generation.

        Constructs a message sequence with the system prompt and context
        from planning and design phases for the frontend developer role.

        Args:
            context: Dict with planner_output, designer_output,
                     template_output, techstack_output from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Planning output (task graph): {context.get('planner_output', {})}\n\n"
                    f"Design output (wireframes/components): {context.get('designer_output', {})}\n\n"
                    f"Template scaffold: {context.get('template_output', {})}\n\n"
                    f"Tech stack configuration: {context.get('techstack_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce frontend code with components, routes, state, and tests.

        In the current implementation, returns a structured placeholder
        that downstream agents (CodeReviewer, Tester) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with frontend code output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "component_tree": {},
                "route_definitions": [],
                "test_stubs": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate frontend output contains generated files.

        Checks that generated_files is a non-empty list where each entry
        has 'path' and 'content' keys.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            frontend_dev_output.
        """
        data = result.data
        generated_files = data.get("generated_files", [])
        review_passed = bool(
            isinstance(generated_files, list)
            and len(generated_files) > 0
            and all(
                isinstance(f, dict) and "path" in f and "content" in f
                for f in generated_files
            )
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"frontend_dev_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Frontend Dev agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
