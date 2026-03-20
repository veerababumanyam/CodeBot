"""MobileDevAgent -- mobile developer for S5 Implementation pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract planner_output, designer_output, api_designer_output,
              techstack_output from shared_state
- reason(): Build LLM message list with mobile development system prompt
- act(): Return structured output with generated files, platform configs,
         navigation tree, and API bindings
- review(): Validate generated_files is a non-empty list

Covers requirement IMPL-03: Cross-platform mobile code generation.
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
You are the Mobile Developer agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage,
executing in parallel with other implementation agents in an isolated git
worktree. Your purpose is to generate cross-platform or native mobile
application code based on the selected tech stack.
</role>

<responsibilities>
- IMPL-03 Mobile Code Generation: Generate mobile application code targeting
  the platform specified in techstack_output. Support React Native, Flutter,
  or native Swift/Kotlin depending on project configuration.
- Screen Implementation: Create screen/page components matching designer
  wireframes and component hierarchy. Implement proper navigation flows
  using the platform's native navigation library (React Navigation, Flutter
  Navigator, UIKit/Jetpack Navigation).
- API Integration: Generate typed API client bindings from api_designer_output
  specifications. Implement proper error handling, retry logic, and offline
  caching patterns appropriate to the mobile platform.
- Platform Configuration: Generate platform-specific configuration files
  including app manifests, build configurations, signing configs, and
  dependency management (CocoaPods/Gradle/pubspec).
- State Management: Set up appropriate state management for the chosen
  platform (Redux/Zustand for React Native, Provider/Riverpod for Flutter,
  SwiftUI/Combine or ViewModel for native).
- Test Generation: Create test stubs for components and screens using
  platform-appropriate testing frameworks (Jest/RTL for RN, widget tests
  for Flutter, XCTest/JUnit for native).
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of objects with "path" and "content" keys
- "platform_configs": object with platform-specific configuration details
- "navigation_tree": hierarchical object describing the navigation structure
- "api_bindings": array of API binding objects with "endpoint", "method",
  and "types" keys
</output_format>

<constraints>
- Target platform must match techstack_output selection
- Use TypeScript strict mode for React Native projects
- Follow platform-specific naming conventions (camelCase for RN, snake_case
  for Flutter, PascalCase for Swift, camelCase for Kotlin)
- Generate platform-specific asset management (image catalogs, font configs)
- Include proper permission declarations in manifests
- Do not hardcode API URLs -- use environment or build configuration
- Ensure proper lifecycle management (mount/unmount, dispose, deinit)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.MOBILE_DEV)
@dataclass(slots=True, kw_only=True)
class MobileDevAgent(BaseAgent):
    """Mobile developer for S5 Implementation pipeline stage.

    Generates cross-platform or native mobile application code based on
    the selected tech stack, including screens, navigation, API bindings,
    and platform configs. Executes in an isolated git worktree for
    parallel safety.

    Attributes:
        agent_type: Always ``AgentType.MOBILE_DEV``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for code generation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether this agent requires worktree isolation.
    """

    agent_type: AgentType = field(default=AgentType.MOBILE_DEV, init=False)
    name: str = "mobile_dev"
    model_tier: str = "tier1"
    max_retries: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "file_edit",
            "bash",
            "simulator_preview",
            "cocoapods",
            "gradle",
        ]
    )
    use_worktree: bool = True

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for MobileDevAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract mobile development context from shared state.

        Pulls planner_output, designer_output, api_designer_output,
        and techstack_output from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planner_output, designer_output, api_designer_output,
            and techstack_output.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "designer_output": shared_state.get("designer_output", {}),
            "api_designer_output": shared_state.get("api_designer_output", {}),
            "techstack_output": shared_state.get("techstack_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for mobile code generation.

        Constructs a message sequence with the system prompt and context
        from planning and design phases for the mobile developer role.

        Args:
            context: Dict with planner_output, designer_output,
                     api_designer_output, techstack_output from perceive().

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
                    f"API design specification: {context.get('api_designer_output', {})}\n\n"
                    f"Tech stack configuration: {context.get('techstack_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce mobile code with screens, navigation, and API bindings.

        In the current implementation, returns a structured placeholder
        that downstream agents (CodeReviewer, Tester) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with mobile code output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "platform_configs": {},
                "navigation_tree": {},
                "api_bindings": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate mobile output contains generated files.

        Checks that generated_files is a non-empty list.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            mobile_dev_output.
        """
        data = result.data
        generated_files = data.get("generated_files", [])
        review_passed = bool(
            isinstance(generated_files, list)
            and len(generated_files) > 0
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"mobile_dev_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Mobile Dev agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
