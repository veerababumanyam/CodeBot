"""InfraEngineerAgent -- infrastructure engineer for S5 Implementation pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract planner_output, architect_output, techstack_output
              from shared_state
- reason(): Build LLM message list with infrastructure engineering system prompt
- act(): Return structured output with generated files, Docker configs,
         CI/CD pipeline, and environment configurations
- review(): Validate generated_files is non-empty and includes at least one
            Dockerfile or docker-compose entry

Covers requirement IMPL-04: Docker, CI/CD, and infrastructure config generation.
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
You are the Infrastructure Engineer agent for CodeBot, a multi-agent software
development platform. You operate in the S5 (Implementation) pipeline stage,
executing in parallel with other implementation agents in an isolated git
worktree. Your purpose is to generate production-grade infrastructure
configuration including Docker, CI/CD pipelines, Kubernetes manifests,
Terraform configs, and environment configuration files.
</role>

<responsibilities>
- IMPL-04 Infrastructure Configuration: Generate Docker, CI/CD pipelines,
  and infrastructure configuration from architecture and planning outputs.
- Docker Configuration: Generate multi-stage Dockerfiles optimized for
  production (small image size, non-root user, health checks). Create
  docker-compose files for local development with proper service
  dependencies, health checks, and volume mounts.
- CI/CD Pipeline: Generate GitHub Actions workflows for build, test, lint,
  and deploy stages. Include proper caching strategies for dependencies.
  Configure matrix builds for multi-platform support where applicable.
- Kubernetes Manifests: Generate Kubernetes deployment, service, ingress,
  and config resources. Include proper resource limits, liveness/readiness
  probes, and horizontal pod autoscaling configurations.
- Terraform Configuration: Generate Terraform modules for cloud infrastructure
  provisioning. Include proper state management, variable definitions, and
  output declarations.
- Environment Configuration: Generate environment-specific configuration
  files (.env templates, config maps) with proper secret management
  patterns (external secret references, not inline secrets).
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "generated_files": array of objects with "path" and "content" keys
- "docker_configs": object with Dockerfile and docker-compose details
- "ci_cd_pipeline": object with GitHub Actions workflow definitions
- "env_configs": object with environment variable templates and configs
</output_format>

<constraints>
- All Dockerfiles must use multi-stage builds
- Never include secrets or credentials in generated files
- Use environment variables or external secret references for sensitive values
- CI/CD workflows must include proper caching for faster builds
- Kubernetes manifests must include resource limits and health probes
- Terraform configs must use remote state (not local)
- Use pinned versions for all base images and tool versions
- Include .dockerignore files to minimize build context size
- Docker containers must run as non-root users
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.INFRA_ENGINEER)
@dataclass(slots=True, kw_only=True)
class InfraEngineerAgent(BaseAgent):
    """Infrastructure engineer for S5 Implementation pipeline stage.

    Generates Docker, CI/CD pipelines, Kubernetes manifests, Terraform
    configs, and environment configuration from architecture and planning
    outputs. Executes in an isolated git worktree for parallel safety.

    Attributes:
        agent_type: Always ``AgentType.INFRA_ENGINEER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for infra generation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether this agent requires worktree isolation.
    """

    agent_type: AgentType = field(default=AgentType.INFRA_ENGINEER, init=False)
    name: str = "infra_engineer"
    model_tier: str = "tier1"
    max_retries: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "bash",
            "terraform_validate",
            "docker_build",
            "kubectl",
            "config_renderer",
        ]
    )
    use_worktree: bool = True

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for InfraEngineerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract infrastructure context from shared state.

        Pulls planner_output, architect_output, and techstack_output
        from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with planner_output, architect_output, and techstack_output.
        """
        shared_state = agent_input.shared_state
        return {
            "planner_output": shared_state.get("planner_output", {}),
            "architect_output": shared_state.get("architect_output", {}),
            "techstack_output": shared_state.get("techstack_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for infrastructure generation.

        Constructs a message sequence with the system prompt and context
        from planning and architecture phases for the infra engineer role.

        Args:
            context: Dict with planner_output, architect_output,
                     techstack_output from perceive().

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
                    f"Tech stack configuration: {context.get('techstack_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce infrastructure configs with Docker, CI/CD, and env files.

        In the current implementation, returns a structured placeholder
        that downstream agents (SecurityAuditor, Tester) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with infrastructure output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
                "docker_configs": {},
                "ci_cd_pipeline": {},
                "env_configs": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate infrastructure output contains Docker configuration.

        Checks that generated_files is non-empty and includes at least one
        Dockerfile or docker-compose entry.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            infra_engineer_output.
        """
        data = result.data
        generated_files = data.get("generated_files", [])
        has_docker = any(
            isinstance(f, dict)
            and ("dockerfile" in f.get("path", "").lower()
                 or "docker-compose" in f.get("path", "").lower())
            for f in generated_files
        )
        review_passed = bool(
            isinstance(generated_files, list)
            and len(generated_files) > 0
            and has_docker
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"infra_engineer_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Infrastructure Engineer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
