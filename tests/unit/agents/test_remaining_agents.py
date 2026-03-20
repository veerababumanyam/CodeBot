"""Unit tests for remaining agents: DevOps, GitHub, Orchestrator, ProjectManager,
CodeReviewer, BackendDev, SkillCreator, HooksCreator, ToolsCreator, CollaborationManager.

Validates agent type, BaseAgent inheritance, registration, stub behavior,
Orchestrator tools (INPT-03/INPT-08), and YAML config loading.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from agent_sdk.agents.base import BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

# Import all agent modules to trigger registration
from codebot.agents.backend_dev import BackendDevAgent
from codebot.agents.code_reviewer import CodeReviewerAgent
from codebot.agents.collaboration_manager import CollaborationManagerAgent
from codebot.agents.devops import DevOpsAgent
from codebot.agents.github_agent import GitHubAgent
from codebot.agents.hooks_creator import HooksCreatorAgent
from codebot.agents.orchestrator import OrchestratorAgent
from codebot.agents.project_manager import ProjectManagerAgent
from codebot.agents.registry import get_all_registered
from codebot.agents.skill_creator import SkillCreatorAgent
from codebot.agents.tools_creator import ToolsCreatorAgent


# ---------------------------------------------------------------------------
# Parametrized agent type and class mapping
# ---------------------------------------------------------------------------

_AGENT_MAP: list[tuple[type, AgentType, str]] = [
    (DevOpsAgent, AgentType.DEPLOYER, "devops"),
    (GitHubAgent, AgentType.GITHUB_INTEGRATOR, "github"),
    (OrchestratorAgent, AgentType.ORCHESTRATOR, "orchestrator"),
    (ProjectManagerAgent, AgentType.PROJECT_MANAGER, "project_manager"),
    (CodeReviewerAgent, AgentType.CODE_REVIEWER, "code_reviewer"),
    (BackendDevAgent, AgentType.BACKEND_DEV, "backend_dev"),
    (SkillCreatorAgent, AgentType.SKILL_MANAGER, "skill_creator"),
    (HooksCreatorAgent, AgentType.HOOK_MANAGER, "hooks_creator"),
    (ToolsCreatorAgent, AgentType.TOOL_BUILDER, "tools_creator"),
    (CollaborationManagerAgent, AgentType.COLLABORATION_MANAGER, "collaboration_manager"),
]


class TestAgentType:
    """Each agent must report the correct AgentType."""

    @pytest.mark.parametrize(
        "cls, expected_type, _name",
        _AGENT_MAP,
        ids=[m[2] for m in _AGENT_MAP],
    )
    def test_agent_type(self, cls: type, expected_type: AgentType, _name: str) -> None:
        agent = cls()
        assert agent.agent_type == expected_type


class TestExtendsBaseAgent:
    """Each agent must extend BaseAgent."""

    @pytest.mark.parametrize(
        "cls, _type, _name",
        _AGENT_MAP,
        ids=[m[2] for m in _AGENT_MAP],
    )
    def test_extends_base_agent(self, cls: type, _type: AgentType, _name: str) -> None:
        agent = cls()
        assert isinstance(agent, BaseAgent)


class TestRegistered:
    """Each agent must be registered in the registry."""

    @pytest.mark.parametrize(
        "cls, expected_type, _name",
        _AGENT_MAP,
        ids=[m[2] for m in _AGENT_MAP],
    )
    def test_registered(self, cls: type, expected_type: AgentType, _name: str) -> None:
        registered = get_all_registered()
        assert expected_type in registered, (
            f"AgentType.{expected_type.name} not found in registry"
        )


class TestToolingStubs:
    """Tooling stubs and CollaborationManager must return stub=True."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cls",
        [SkillCreatorAgent, HooksCreatorAgent, ToolsCreatorAgent, CollaborationManagerAgent],
        ids=["skill_creator", "hooks_creator", "tools_creator", "collaboration_manager"],
    )
    async def test_stub_returns_stub_flag(self, cls: type) -> None:
        agent = cls()
        result: PRAResult = await agent.act({})
        assert result.data.get("stub") is True


class TestOrchestratorTools:
    """OrchestratorAgent must have specific tools for INPT-03 and INPT-08."""

    def test_orchestrator_has_git_importer_tool(self) -> None:
        """INPT-08: OrchestratorAgent must have git_importer tool."""
        agent = OrchestratorAgent()
        assert "git_importer" in agent.tools

    def test_orchestrator_has_multimodal_tool(self) -> None:
        """INPT-03: OrchestratorAgent must have multimodal_input_processor tool."""
        agent = OrchestratorAgent()
        assert "multimodal_input_processor" in agent.tools

    def test_orchestrator_has_local_codebase_loader(self) -> None:
        """INPT-08: OrchestratorAgent must have local_codebase_loader tool."""
        agent = OrchestratorAgent()
        assert "local_codebase_loader" in agent.tools


class TestBackendDevWorktree:
    """BackendDevAgent must have use_worktree=True for parallel execution."""

    def test_backend_dev_use_worktree(self) -> None:
        agent = BackendDevAgent()
        assert agent.use_worktree is True


class TestYamlConfigsLoad:
    """All YAML config files for the 10 remaining agents must load correctly."""

    _CONFIG_MAP: list[tuple[str, str]] = [
        ("devops.yaml", "DEPLOYER"),
        ("github.yaml", "GITHUB_INTEGRATOR"),
        ("orchestrator.yaml", "ORCHESTRATOR"),
        ("project_manager.yaml", "PROJECT_MANAGER"),
        ("code_reviewer.yaml", "CODE_REVIEWER"),
        ("backend_dev.yaml", "BACKEND_DEV"),
        ("skill_creator.yaml", "SKILL_MANAGER"),
        ("hooks_creator.yaml", "HOOK_MANAGER"),
        ("tools_creator.yaml", "TOOL_BUILDER"),
        ("collaboration_manager.yaml", "COLLABORATION_MANAGER"),
    ]

    @pytest.mark.parametrize(
        "filename, expected_type",
        _CONFIG_MAP,
        ids=[c[0].replace(".yaml", "") for c in _CONFIG_MAP],
    )
    def test_yaml_configs_load_all(self, filename: str, expected_type: str) -> None:
        config_path = Path("configs/agents") / filename
        assert config_path.exists(), f"Config file not found: {config_path}"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        # Config should have a top-level key and contain agent_type
        assert config is not None
        top_key = list(config.keys())[0]
        assert config[top_key]["agent_type"] == expected_type
