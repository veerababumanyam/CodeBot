"""Unit tests for S5 Implementation stage agents.

Tests FrontendDevAgent, MobileDevAgent, InfraEngineerAgent, MiddlewareDevAgent,
and IntegrationsAgent for:
- Correct AgentType values
- BaseAgent inheritance
- Worktree isolation flag
- Review pass/fail with generated_files
- Distinct SharedState keys for parallel safety
- YAML config loading
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from agent_sdk.agents.base import AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.frontend_dev import FrontendDevAgent
from codebot.agents.infra_engineer import InfraEngineerAgent
from codebot.agents.integrations import IntegrationsAgent
from codebot.agents.middleware_dev import MiddlewareDevAgent
from codebot.agents.mobile_dev import MobileDevAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def frontend_agent() -> FrontendDevAgent:
    """Create a FrontendDevAgent instance."""
    return FrontendDevAgent()


@pytest.fixture
def mobile_agent() -> MobileDevAgent:
    """Create a MobileDevAgent instance."""
    return MobileDevAgent()


@pytest.fixture
def infra_agent() -> InfraEngineerAgent:
    """Create an InfraEngineerAgent instance."""
    return InfraEngineerAgent()


@pytest.fixture
def middleware_agent() -> MiddlewareDevAgent:
    """Create a MiddlewareDevAgent instance."""
    return MiddlewareDevAgent()


@pytest.fixture
def integrations_agent() -> IntegrationsAgent:
    """Create an IntegrationsAgent instance."""
    return IntegrationsAgent()


# ---------------------------------------------------------------------------
# FrontendDevAgent tests
# ---------------------------------------------------------------------------


class TestFrontendDevAgentType:
    """FrontendDevAgent has correct type and inheritance."""

    def test_frontend_dev_agent_type(self, frontend_agent: FrontendDevAgent) -> None:
        """agent_type is FRONTEND_DEV."""
        assert frontend_agent.agent_type == AgentType.FRONTEND_DEV

    def test_frontend_dev_extends_base_agent(self, frontend_agent: FrontendDevAgent) -> None:
        """FrontendDevAgent is a subclass of BaseAgent."""
        assert isinstance(frontend_agent, BaseAgent)

    def test_frontend_dev_use_worktree_true(self, frontend_agent: FrontendDevAgent) -> None:
        """use_worktree is True for parallel worktree safety."""
        assert frontend_agent.use_worktree is True


class TestFrontendDevReview:
    """FrontendDevAgent.review() validates output."""

    async def test_frontend_dev_review_passes_with_generated_files(
        self, frontend_agent: FrontendDevAgent
    ) -> None:
        """review() returns review_passed=True when generated_files is non-empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "src/App.tsx", "content": "export default App;"}],
                "component_tree": {},
                "route_definitions": [],
                "test_stubs": [],
            },
        )
        output = await frontend_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_frontend_dev_review_fails_with_empty_files(
        self, frontend_agent: FrontendDevAgent
    ) -> None:
        """review() returns review_passed=False when generated_files is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"generated_files": []},
        )
        output = await frontend_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestFrontendDevStateUpdates:
    """review() stores output under frontend_dev_output key."""

    async def test_state_updates_use_frontend_dev_output_key(
        self, frontend_agent: FrontendDevAgent
    ) -> None:
        """state_updates contains frontend_dev_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "x", "content": "y"}],
            },
        )
        output = await frontend_agent.review(pra_result)
        assert "frontend_dev_output" in output.state_updates


# ---------------------------------------------------------------------------
# MobileDevAgent tests
# ---------------------------------------------------------------------------


class TestMobileDevAgentType:
    """MobileDevAgent has correct type and inheritance."""

    def test_mobile_dev_agent_type(self, mobile_agent: MobileDevAgent) -> None:
        """agent_type is MOBILE_DEV."""
        assert mobile_agent.agent_type == AgentType.MOBILE_DEV

    def test_mobile_dev_extends_base_agent(self, mobile_agent: MobileDevAgent) -> None:
        """MobileDevAgent is a subclass of BaseAgent."""
        assert isinstance(mobile_agent, BaseAgent)

    def test_mobile_dev_use_worktree_true(self, mobile_agent: MobileDevAgent) -> None:
        """use_worktree is True for parallel worktree safety."""
        assert mobile_agent.use_worktree is True


class TestMobileDevReview:
    """MobileDevAgent.review() validates output."""

    async def test_mobile_dev_review_passes_with_generated_files(
        self, mobile_agent: MobileDevAgent
    ) -> None:
        """review() returns review_passed=True when generated_files is non-empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "src/App.tsx", "content": "export default App;"}],
                "platform_configs": {},
                "navigation_tree": {},
                "api_bindings": [],
            },
        )
        output = await mobile_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_mobile_dev_review_fails_with_empty_files(
        self, mobile_agent: MobileDevAgent
    ) -> None:
        """review() returns review_passed=False when generated_files is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"generated_files": []},
        )
        output = await mobile_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestMobileDevStateUpdates:
    """review() stores output under mobile_dev_output key."""

    async def test_state_updates_use_mobile_dev_output_key(
        self, mobile_agent: MobileDevAgent
    ) -> None:
        """state_updates contains mobile_dev_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "x", "content": "y"}],
            },
        )
        output = await mobile_agent.review(pra_result)
        assert "mobile_dev_output" in output.state_updates


# ---------------------------------------------------------------------------
# InfraEngineerAgent tests
# ---------------------------------------------------------------------------


class TestInfraEngineerAgentType:
    """InfraEngineerAgent has correct type and inheritance."""

    def test_infra_engineer_agent_type(self, infra_agent: InfraEngineerAgent) -> None:
        """agent_type is INFRA_ENGINEER."""
        assert infra_agent.agent_type == AgentType.INFRA_ENGINEER

    def test_infra_engineer_extends_base_agent(self, infra_agent: InfraEngineerAgent) -> None:
        """InfraEngineerAgent is a subclass of BaseAgent."""
        assert isinstance(infra_agent, BaseAgent)

    def test_infra_engineer_use_worktree_true(self, infra_agent: InfraEngineerAgent) -> None:
        """use_worktree is True for parallel worktree safety."""
        assert infra_agent.use_worktree is True


class TestInfraEngineerReview:
    """InfraEngineerAgent.review() validates output."""

    async def test_infra_engineer_review_passes_with_generated_files(
        self, infra_agent: InfraEngineerAgent
    ) -> None:
        """review() returns review_passed=True when generated_files has Docker config."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [
                    {"path": "Dockerfile", "content": "FROM python:3.12-slim"},
                    {"path": "docker-compose.yml", "content": "version: '3.8'"},
                ],
                "docker_configs": {},
                "ci_cd_pipeline": {},
                "env_configs": {},
            },
        )
        output = await infra_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_infra_engineer_review_fails_with_empty_files(
        self, infra_agent: InfraEngineerAgent
    ) -> None:
        """review() returns review_passed=False when generated_files is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"generated_files": []},
        )
        output = await infra_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False

    async def test_infra_engineer_review_fails_without_docker(
        self, infra_agent: InfraEngineerAgent
    ) -> None:
        """review() returns review_passed=False when no Docker config present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [
                    {"path": "terraform/main.tf", "content": "provider \"aws\" {}"},
                ],
            },
        )
        output = await infra_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestInfraEngineerStateUpdates:
    """review() stores output under infra_engineer_output key."""

    async def test_state_updates_use_infra_engineer_output_key(
        self, infra_agent: InfraEngineerAgent
    ) -> None:
        """state_updates contains infra_engineer_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "Dockerfile", "content": "FROM alpine"}],
            },
        )
        output = await infra_agent.review(pra_result)
        assert "infra_engineer_output" in output.state_updates


# ---------------------------------------------------------------------------
# YAML config tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# MiddlewareDevAgent tests
# ---------------------------------------------------------------------------


class TestMiddlewareDevAgentType:
    """MiddlewareDevAgent has correct type and inheritance."""

    def test_middleware_dev_agent_type(self, middleware_agent: MiddlewareDevAgent) -> None:
        """agent_type is MIDDLEWARE_DEV."""
        assert middleware_agent.agent_type == AgentType.MIDDLEWARE_DEV

    def test_middleware_dev_extends_base_agent(self, middleware_agent: MiddlewareDevAgent) -> None:
        """MiddlewareDevAgent is a subclass of BaseAgent."""
        assert isinstance(middleware_agent, BaseAgent)

    def test_middleware_dev_use_worktree_true(self, middleware_agent: MiddlewareDevAgent) -> None:
        """use_worktree is True for parallel worktree safety."""
        assert middleware_agent.use_worktree is True


class TestMiddlewareDevReview:
    """MiddlewareDevAgent.review() validates output."""

    async def test_middleware_dev_review_passes_with_generated_files(
        self, middleware_agent: MiddlewareDevAgent
    ) -> None:
        """review() returns review_passed=True when generated_files is non-empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "src/middleware/auth.py", "content": "class AuthMiddleware: ..."}],
                "middleware_stack": {},
                "api_routes": [],
                "auth_config": {},
            },
        )
        output = await middleware_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_middleware_dev_review_fails_with_empty_files(
        self, middleware_agent: MiddlewareDevAgent
    ) -> None:
        """review() returns review_passed=False when generated_files is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"generated_files": []},
        )
        output = await middleware_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestMiddlewareDevStateUpdates:
    """review() stores output under middleware_dev_output key."""

    async def test_state_updates_use_middleware_dev_output_key(
        self, middleware_agent: MiddlewareDevAgent
    ) -> None:
        """state_updates contains middleware_dev_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "x", "content": "y"}],
            },
        )
        output = await middleware_agent.review(pra_result)
        assert "middleware_dev_output" in output.state_updates


# ---------------------------------------------------------------------------
# IntegrationsAgent tests
# ---------------------------------------------------------------------------


class TestIntegrationsAgentType:
    """IntegrationsAgent has correct type and inheritance."""

    def test_integrations_agent_type(self, integrations_agent: IntegrationsAgent) -> None:
        """agent_type is INTEGRATION_ADAPTER."""
        assert integrations_agent.agent_type == AgentType.INTEGRATION_ADAPTER

    def test_integrations_extends_base_agent(self, integrations_agent: IntegrationsAgent) -> None:
        """IntegrationsAgent is a subclass of BaseAgent."""
        assert isinstance(integrations_agent, BaseAgent)

    def test_integrations_use_worktree_true(self, integrations_agent: IntegrationsAgent) -> None:
        """use_worktree is True for parallel worktree safety."""
        assert integrations_agent.use_worktree is True


class TestIntegrationsReview:
    """IntegrationsAgent.review() validates output."""

    async def test_integrations_review_passes_with_generated_files(
        self, integrations_agent: IntegrationsAgent
    ) -> None:
        """review() returns review_passed=True when generated_files is non-empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "src/integrations/stripe.py", "content": "class StripeClient: ..."}],
                "api_clients": [],
                "webhook_handlers": [],
                "sdk_wrappers": [],
            },
        )
        output = await integrations_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_integrations_review_fails_with_empty_files(
        self, integrations_agent: IntegrationsAgent
    ) -> None:
        """review() returns review_passed=False when generated_files is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"generated_files": []},
        )
        output = await integrations_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestIntegrationsStateUpdates:
    """review() stores output under integrations_output key."""

    async def test_state_updates_use_integrations_output_key(
        self, integrations_agent: IntegrationsAgent
    ) -> None:
        """state_updates contains integrations_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "x", "content": "y"}],
            },
        )
        output = await integrations_agent.review(pra_result)
        assert "integrations_output" in output.state_updates


# ---------------------------------------------------------------------------
# Cross-cutting S5 tests
# ---------------------------------------------------------------------------


class TestAllS5AgentsWriteDifferentStateKeys:
    """All 5 S5 agents write to distinct SharedState namespaces."""

    async def test_all_s5_agents_write_different_state_keys(self) -> None:
        """All 5 S5 agents produce distinct state_updates keys."""
        agents = [
            FrontendDevAgent(),
            MobileDevAgent(),
            InfraEngineerAgent(),
            MiddlewareDevAgent(),
            IntegrationsAgent(),
        ]

        state_keys: set[str] = set()
        for agent in agents:
            # Build a PRAResult that passes review for each agent
            if isinstance(agent, InfraEngineerAgent):
                data = {"generated_files": [{"path": "Dockerfile", "content": "FROM alpine"}]}
            else:
                data = {"generated_files": [{"path": "x", "content": "y"}]}

            pra_result = PRAResult(is_complete=True, data=data)
            output = await agent.review(pra_result)
            state_keys.update(output.state_updates.keys())

        expected_keys = {
            "frontend_dev_output",
            "mobile_dev_output",
            "infra_engineer_output",
            "middleware_dev_output",
            "integrations_output",
        }
        assert state_keys == expected_keys


# ---------------------------------------------------------------------------
# YAML config tests
# ---------------------------------------------------------------------------


class TestYAMLConfigsLoad:
    """YAML configs for all 5 S5 agents load and validate."""

    def test_frontend_dev_yaml_config_loads(self) -> None:
        """frontend_dev.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "frontend_dev.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["agent"]["type"] == "FRONTEND_DEV"

    def test_mobile_dev_yaml_config_loads(self) -> None:
        """mobile_dev.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "mobile_dev.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["agent"]["type"] == "MOBILE_DEV"

    def test_infra_engineer_yaml_config_loads(self) -> None:
        """infra_engineer.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "infra_engineer.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["agent"]["type"] == "INFRA_ENGINEER"

    def test_middleware_dev_yaml_config_loads(self) -> None:
        """middleware_dev.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "middleware_dev.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["agent"]["type"] == "MIDDLEWARE_DEV"

    def test_integrations_yaml_config_loads(self) -> None:
        """integrations.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "integrations.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["agent"]["type"] == "INTEGRATION_ADAPTER"
