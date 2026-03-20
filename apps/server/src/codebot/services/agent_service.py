"""Agent lifecycle management service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.schemas.agents import AgentConfigUpdate
from codebot.db.models.agent import Agent, AgentStatus, AgentType


class AgentService:
    """Business logic for agent lifecycle operations.

    Args:
        db: Async database session.
    """

    # Statuses from which an agent can be started
    VALID_START_FROM: set[AgentStatus] = {AgentStatus.IDLE, AgentStatus.TERMINATED}

    # Statuses from which an agent can be stopped
    VALID_STOP_FROM: set[AgentStatus] = {
        AgentStatus.RUNNING,
        AgentStatus.WAITING,
        AgentStatus.INITIALIZING,
    }

    # Statuses from which an agent can be restarted
    VALID_RESTART_FROM: set[AgentStatus] = {
        AgentStatus.TERMINATED,
        AgentStatus.FAILED,
        AgentStatus.COMPLETED,
    }

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_agents(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        project_id: UUID | None = None,
        status: str | None = None,
        agent_type: str | None = None,
    ) -> tuple[list[Agent], int]:
        """List agents with optional filters.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            project_id: Optional project filter.
            status: Optional status filter (case-insensitive).
            agent_type: Optional agent type filter (case-insensitive).

        Returns:
            Tuple of (agents list, total count).
        """
        query = select(Agent)
        count_query = select(func.count()).select_from(Agent)

        if project_id is not None:
            query = query.where(Agent.project_id == project_id)
            count_query = count_query.where(Agent.project_id == project_id)

        if status is not None:
            try:
                status_enum = AgentStatus(status.upper())
            except ValueError:
                status_enum = None
            if status_enum is not None:
                query = query.where(Agent.status == status_enum)
                count_query = count_query.where(Agent.status == status_enum)

        if agent_type is not None:
            try:
                type_enum = AgentType(agent_type.upper())
            except ValueError:
                type_enum = None
            if type_enum is not None:
                query = query.where(Agent.agent_type == type_enum)
                count_query = count_query.where(Agent.agent_type == type_enum)

        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        result = await self._db.execute(query)
        agents = list(result.scalars().all())

        return agents, int(total)

    async def get(self, agent_id: UUID) -> Agent | None:
        """Get an agent by ID.

        Args:
            agent_id: The agent's UUID.

        Returns:
            The Agent if found, else None.
        """
        return await self._db.get(Agent, agent_id)

    async def start(self, agent: Agent) -> Agent:
        """Start an agent (transition from IDLE/TERMINATED to RUNNING).

        Args:
            agent: The Agent ORM object.

        Returns:
            The updated Agent.

        Raises:
            HTTPException: 400 if agent cannot be started from current state.
        """
        if agent.status not in self.VALID_START_FROM:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start agent in {agent.status.value} state",
            )

        agent.status = AgentStatus.RUNNING
        agent.started_at = datetime.now(UTC)
        agent.completed_at = None

        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def stop(
        self,
        agent: Agent,
        reason: str | None = None,
        force: bool = False,
    ) -> Agent:
        """Stop an agent (transition from RUNNING/WAITING/INITIALIZING to TERMINATED).

        Args:
            agent: The Agent ORM object.
            reason: Optional reason for stopping.
            force: Whether to force stop.

        Returns:
            The updated Agent.

        Raises:
            HTTPException: 400 if agent cannot be stopped from current state.
        """
        if agent.status not in self.VALID_STOP_FROM:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot stop agent in {agent.status.value} state",
            )

        agent.status = AgentStatus.TERMINATED
        agent.completed_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def restart(self, agent: Agent) -> Agent:
        """Restart an agent (transition from TERMINATED/FAILED/COMPLETED to RUNNING).

        Args:
            agent: The Agent ORM object.

        Returns:
            The updated Agent.

        Raises:
            HTTPException: 400 if agent cannot be restarted from current state.
        """
        if agent.status not in self.VALID_RESTART_FROM:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot restart agent in {agent.status.value} state",
            )

        agent.status = AgentStatus.RUNNING
        agent.started_at = datetime.now(UTC)
        agent.completed_at = None

        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def configure(self, agent: Agent, config: AgentConfigUpdate) -> Agent:
        """Update agent configuration (model, provider, etc.).

        Cannot be called while the agent is RUNNING.

        Args:
            agent: The Agent ORM object.
            config: Configuration update payload.

        Returns:
            The updated Agent.

        Raises:
            HTTPException: 400 if agent is currently RUNNING.
        """
        if agent.status == AgentStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail="Cannot configure agent while running",
            )

        if config.llm_provider is not None:
            agent.llm_provider = config.llm_provider
        if config.llm_model is not None:
            agent.llm_model = config.llm_model
        if config.system_prompt is not None:
            agent.system_prompt_hash = hashlib.sha256(
                config.system_prompt.encode()
            ).hexdigest()

        await self._db.commit()
        await self._db.refresh(agent)
        return agent

    async def get_agent_types(self) -> list[dict]:
        """Return information about all available agent types.

        Returns:
            List of agent type info dictionaries.
        """
        type_info: dict[str, dict] = {
            "ORCHESTRATOR": {
                "display_name": "Orchestrator",
                "description": "Coordinates the overall pipeline execution and agent lifecycle",
                "category": "control",
                "capabilities": ["pipeline_management", "agent_coordination", "state_tracking"],
            },
            "PLANNER": {
                "display_name": "Planner",
                "description": "Creates implementation plans and task breakdowns",
                "category": "planning",
                "capabilities": ["task_decomposition", "dependency_analysis", "effort_estimation"],
            },
            "RESEARCHER": {
                "display_name": "Researcher",
                "description": "Researches technologies, patterns, and best practices",
                "category": "planning",
                "capabilities": ["technology_research", "pattern_analysis", "recommendation"],
            },
            "ARCHITECT": {
                "display_name": "Architect",
                "description": "Designs system architecture and component structure",
                "category": "design",
                "capabilities": ["system_design", "component_modeling", "api_design"],
            },
            "DESIGNER": {
                "display_name": "Designer",
                "description": "Creates UI/UX designs and design system components",
                "category": "design",
                "capabilities": ["ui_design", "ux_design", "design_system"],
            },
            "API_DESIGNER": {
                "display_name": "API Designer",
                "description": "Designs RESTful and GraphQL API specifications",
                "category": "design",
                "capabilities": ["api_specification", "schema_design", "endpoint_design"],
            },
            "FRONTEND_DEV": {
                "display_name": "Frontend Developer",
                "description": "Implements frontend components and pages",
                "category": "development",
                "capabilities": ["react_development", "css_styling", "component_creation"],
            },
            "BACKEND_DEV": {
                "display_name": "Backend Developer",
                "description": "Implements backend services and API endpoints",
                "category": "development",
                "capabilities": ["api_implementation", "database_queries", "business_logic"],
            },
            "MIDDLEWARE_DEV": {
                "display_name": "Middleware Developer",
                "description": "Implements middleware, integrations, and data pipelines",
                "category": "development",
                "capabilities": ["middleware_creation", "data_pipeline", "integration"],
            },
            "MOBILE_DEV": {
                "display_name": "Mobile Developer",
                "description": "Implements mobile applications (React Native, Flutter)",
                "category": "development",
                "capabilities": ["mobile_development", "cross_platform", "native_features"],
            },
            "INFRA_ENGINEER": {
                "display_name": "Infrastructure Engineer",
                "description": "Creates infrastructure code and deployment scripts",
                "category": "development",
                "capabilities": ["docker_config", "ci_cd", "iac"],
            },
            "CODE_REVIEWER": {
                "display_name": "Code Reviewer",
                "description": "Reviews code for quality, patterns, and best practices",
                "category": "quality",
                "capabilities": ["code_review", "pattern_detection", "quality_assessment"],
            },
            "SECURITY_AUDITOR": {
                "display_name": "Security Auditor",
                "description": "Scans code for security vulnerabilities and compliance issues",
                "category": "quality",
                "capabilities": ["vulnerability_scanning", "compliance_check", "security_review"],
            },
            "TESTER": {
                "display_name": "Tester",
                "description": "Writes and runs unit, integration, and E2E tests",
                "category": "quality",
                "capabilities": ["unit_testing", "integration_testing", "e2e_testing"],
            },
            "DEBUGGER": {
                "display_name": "Debugger",
                "description": "Diagnoses and fixes bugs found during testing",
                "category": "quality",
                "capabilities": ["bug_diagnosis", "root_cause_analysis", "fix_implementation"],
            },
            "PERFORMANCE_TESTER": {
                "display_name": "Performance Tester",
                "description": "Runs performance benchmarks and identifies bottlenecks",
                "category": "quality",
                "capabilities": ["load_testing", "benchmarking", "performance_analysis"],
            },
            "ACCESSIBILITY_AUDITOR": {
                "display_name": "Accessibility Auditor",
                "description": "Audits applications for accessibility compliance (WCAG)",
                "category": "quality",
                "capabilities": ["wcag_audit", "screen_reader_testing", "accessibility_report"],
            },
            "I18N_SPECIALIST": {
                "display_name": "Internationalization Specialist",
                "description": "Implements internationalization and localization support",
                "category": "quality",
                "capabilities": ["i18n_setup", "locale_management", "translation_workflow"],
            },
            "DOC_WRITER": {
                "display_name": "Documentation Writer",
                "description": "Generates API docs, READMEs, and user guides",
                "category": "documentation",
                "capabilities": ["api_documentation", "readme_generation", "user_guides"],
            },
            "PROJECT_MANAGER": {
                "display_name": "Project Manager",
                "description": "Tracks project progress and manages deliverables",
                "category": "management",
                "capabilities": ["progress_tracking", "deliverable_management", "reporting"],
            },
            "COLLABORATION_MANAGER": {
                "display_name": "Collaboration Manager",
                "description": "Manages real-time collaboration and conflict resolution",
                "category": "management",
                "capabilities": ["conflict_resolution", "crdt_management", "session_management"],
            },
            "BRAINSTORM_FACILITATOR": {
                "display_name": "Brainstorm Facilitator",
                "description": "Facilitates brainstorming sessions and idea generation",
                "category": "planning",
                "capabilities": [
                    "idea_generation",
                    "requirement_elicitation",
                    "feasibility_analysis",
                ],
            },
            "TECH_STACK_ADVISOR": {
                "display_name": "Tech Stack Advisor",
                "description": "Recommends technology stack based on project requirements",
                "category": "planning",
                "capabilities": [
                    "stack_recommendation",
                    "technology_comparison",
                    "compatibility_check",
                ],
            },
            "TEMPLATE_CURATOR": {
                "display_name": "Template Curator",
                "description": "Manages and recommends project templates",
                "category": "planning",
                "capabilities": [
                    "template_selection",
                    "template_customization",
                    "scaffold_generation",
                ],
            },
            "DEPLOYER": {
                "display_name": "Deployer",
                "description": "Deploys applications to cloud environments",
                "category": "development",
                "capabilities": ["cloud_deployment", "environment_management", "rollback"],
            },
            "GITHUB_INTEGRATOR": {
                "display_name": "GitHub Integrator",
                "description": "Manages GitHub repositories, PRs, and CI/CD workflows",
                "category": "management",
                "capabilities": ["repository_management", "pr_creation", "ci_cd_integration"],
            },
            "SKILL_MANAGER": {
                "display_name": "Skill Manager",
                "description": "Manages agent skill extensions and plugins",
                "category": "extensibility",
                "capabilities": ["skill_discovery", "skill_installation", "skill_configuration"],
            },
            "HOOK_MANAGER": {
                "display_name": "Hook Manager",
                "description": "Manages lifecycle hooks and event handlers",
                "category": "extensibility",
                "capabilities": ["hook_registration", "event_handling", "lifecycle_management"],
            },
            "TOOL_BUILDER": {
                "display_name": "Tool Builder",
                "description": "Creates custom tools and utilities for agents",
                "category": "extensibility",
                "capabilities": ["tool_creation", "tool_testing", "tool_publishing"],
            },
            "INTEGRATION_ADAPTER": {
                "display_name": "Integration Adapter",
                "description": "Adapts external services and APIs for agent use",
                "category": "extensibility",
                "capabilities": ["api_adaptation", "service_integration", "data_transformation"],
            },
        }

        result = []
        for member in AgentType:
            info = type_info.get(member.value, {
                "display_name": member.value.replace("_", " ").title(),
                "description": f"{member.value.replace('_', ' ').title()} agent",
                "category": "other",
                "capabilities": [],
            })
            result.append({
                "type": member.value.lower(),
                "display_name": info["display_name"],
                "description": info["description"],
                "category": info["category"],
                "capabilities": info["capabilities"],
            })

        return result
