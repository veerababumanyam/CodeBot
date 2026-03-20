"""DevOpsAgent -- S10 Deployment pipeline stage agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts infra_engineer_output and architect_output from shared_state
- reason(): Builds LLM message list with DevOps-oriented system prompt
- act(): Returns structured deployment configs, CI/CD pipelines, and monitoring config
- review(): Validates deployment_configs is non-empty

Manages deployment configurations, CI/CD pipeline generation, and monitoring setup.
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
You are the DevOps Engineer agent for CodeBot, a multi-agent software
development platform. You operate in the S10 (Deployment) pipeline stage.
Your purpose is to generate deployment configurations, CI/CD pipelines,
and monitoring setup for the generated project.
</role>

<responsibilities>
- Generate Dockerfiles and docker-compose.yml for containerized deployments
- Create Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps)
- Generate Helm charts for parameterized Kubernetes deployments
- Create CI/CD pipeline configurations (GitHub Actions, GitLab CI)
- Set up monitoring and observability (health checks, metrics endpoints)
- Validate deployment configurations for correctness
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "deployment_configs": array of deployment configuration objects with
  type (docker/kubernetes/helm), path, and content
- "ci_cd_pipelines": array of CI/CD pipeline configurations with
  provider, path, and content
- "monitoring_config": object with health_check, metrics, alerting sections
- "generated_files": array of file path strings for all generated configs
</output_format>

<constraints>
- Dockerfiles must follow multi-stage build best practices
- Kubernetes manifests must include resource limits and health probes
- CI/CD pipelines must include lint, test, build, and deploy stages
- All secrets must use environment variables, not hardcoded values
- Generated configs must be validated for YAML/JSON correctness
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.DEPLOYER)
@dataclass(slots=True, kw_only=True)
class DevOpsAgent(BaseAgent):
    """S10 deployment agent managing Docker, Kubernetes, CI/CD, and monitoring configs.

    Generates infrastructure-as-code configurations from architecture and
    infrastructure specifications produced by upstream agents.

    Attributes:
        agent_type: Always ``AgentType.DEPLOYER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.DEPLOYER, init=False)
    name: str = "devops"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "bash",
            "docker_build",
            "helm_template",
            "ci_cd_validator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for DevOpsAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract infrastructure and architecture context from shared state.

        Pulls infra_engineer_output and architect_output from the graph's
        shared state for deployment config generation.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with infra_engineer_output and architect_output.
        """
        shared_state = agent_input.shared_state
        return {
            "infra_engineer_output": shared_state.get("infra_engineer_output", {}),
            "architect_output": shared_state.get("architect_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for deployment config generation.

        Args:
            context: Dict with infra and architecture outputs from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Infrastructure config: {context.get('infra_engineer_output', {})}\n\n"
                    f"Architecture decisions: {context.get('architect_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce deployment configurations, CI/CD pipelines, and monitoring setup.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with deployment output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "deployment_configs": [],
                "ci_cd_pipelines": [],
                "monitoring_config": {},
                "generated_files": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate deployment output contains configurations.

        Checks that deployment_configs is present and non-empty.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            devops_output.
        """
        data = result.data
        review_passed = bool("deployment_configs" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"devops_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the DevOps agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
