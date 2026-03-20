"""GitHubAgent -- GitHub integration specialist for the CodeBot pipeline.

Implements the PRA cognitive cycle:
- perceive(): Extracts tester_output, debugger_output, and project config from shared_state
- reason(): Builds LLM message list with GitHub integration-oriented system prompt
- act(): Returns structured output with pull requests, issues, releases, and webhook configs
- review(): Validates output is well-formed

Creates PRs, manages issues, handles webhook events, and prepares releases.
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
You are the GitHub Integration Specialist agent for CodeBot, a multi-agent
software development platform. Your purpose is to manage all GitHub-related
operations for generated projects.
</role>

<responsibilities>
- Create pull requests with descriptive titles, bodies, and proper branch management
- Manage GitHub issues: create, label, assign, and close based on pipeline events
- Handle webhook events for CI/CD triggers and external integrations
- Prepare releases with semantic versioning, changelogs, and release assets
- Configure branch protection rules and review requirements
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "pull_requests": array of PR objects with title, body, base, head, labels
- "issues": array of issue objects with title, body, labels, assignees
- "releases": array of release objects with tag, name, body, assets
- "webhook_configs": array of webhook configuration objects with url, events, secret
</output_format>

<constraints>
- PR titles must follow conventional commits format
- Release tags must follow semantic versioning (vX.Y.Z)
- Webhook secrets must use environment variables, not hardcoded values
- Issue labels must be from a predefined set (bug, feature, enhancement, documentation)
- All operations must be idempotent where possible
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.GITHUB_INTEGRATOR)
@dataclass(slots=True, kw_only=True)
class GitHubAgent(BaseAgent):
    """GitHub integration specialist for PR creation, issue management, and releases.

    Consumes test and debug outputs to create PRs, manage issues, configure
    webhooks, and prepare releases for the generated project.

    Attributes:
        agent_type: Always ``AgentType.GITHUB_INTEGRATOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.GITHUB_INTEGRATOR, init=False)
    name: str = "github_integrator"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "github_api",
            "pr_creator",
            "issue_tracker",
            "webhook_manager",
            "release_manager",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for GitHubAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract test/debug outputs and project config from shared state.

        Pulls tester_output, debugger_output, and project configuration
        for repository URL from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with tester_output, debugger_output, and project_config.
        """
        shared_state = agent_input.shared_state
        return {
            "tester_output": shared_state.get("tester_output", {}),
            "debugger_output": shared_state.get("debugger_output", {}),
            "project_config": shared_state.get("project_config", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for GitHub operations planning.

        Args:
            context: Dict with test/debug outputs and project config from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Test results: {context.get('tester_output', {})}\n\n"
                    f"Debug results: {context.get('debugger_output', {})}\n\n"
                    f"Project config: {context.get('project_config', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce GitHub operations output with PRs, issues, releases, and webhooks.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with GitHub operations output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "pull_requests": [],
                "issues": [],
                "releases": [],
                "webhook_configs": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate GitHub operations output is well-formed.

        Checks that all expected keys are present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            github_output.
        """
        data = result.data
        review_passed = bool(
            "pull_requests" in data
            and "issues" in data
            and "releases" in data
            and "webhook_configs" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"github_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the GitHub agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
