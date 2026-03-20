"""Unit tests for S3 Architecture agents (Architect, Designer, Template, Database, API)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.api_designer import APIDesignerAgent
from codebot.agents.api_designer import SYSTEM_PROMPT as API_SYSTEM_PROMPT
from codebot.agents.architect import ArchitectAgent
from codebot.agents.architect import SYSTEM_PROMPT as ARCHITECT_SYSTEM_PROMPT
from codebot.agents.database_designer import DatabaseDesignerAgent
from codebot.agents.database_designer import SYSTEM_PROMPT as DB_SYSTEM_PROMPT
from codebot.agents.designer import DesignerAgent
from codebot.agents.designer import SYSTEM_PROMPT as DESIGNER_SYSTEM_PROMPT
from codebot.agents.template_curator import TemplateCuratorAgent
from codebot.agents.template_curator import SYSTEM_PROMPT as TEMPLATE_SYSTEM_PROMPT

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def architect_agent() -> ArchitectAgent:
    """Create an ArchitectAgent instance."""
    return ArchitectAgent()


@pytest.fixture
def designer_agent() -> DesignerAgent:
    """Create a DesignerAgent instance."""
    return DesignerAgent()


@pytest.fixture
def template_agent() -> TemplateCuratorAgent:
    """Create a TemplateCuratorAgent instance."""
    return TemplateCuratorAgent()


@pytest.fixture
def database_agent() -> DatabaseDesignerAgent:
    """Create a DatabaseDesignerAgent instance."""
    return DatabaseDesignerAgent()


@pytest.fixture
def api_agent() -> APIDesignerAgent:
    """Create an APIDesignerAgent instance."""
    return APIDesignerAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput for S3 agents."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "research_output": {"library_evaluations": [], "research_report": "summary"},
            "project_requirements": {"name": "test project"},
            "tech_stack": {"language": "python", "framework": "fastapi"},
            "architect_output": {"architecture_doc": "arch doc"},
            "designer_output": {"wireframes": []},
            "database_output": {"database_schema": {}},
            "user_preferences": {"template": "shadcn-ui"},
        },
        context_tiers={},
    )


# ---------------------------------------------------------------------------
# ArchitectAgent tests
# ---------------------------------------------------------------------------


class TestArchitectAgentType:
    """ArchitectAgent has correct type and inheritance."""

    def test_architect_agent_type(self, architect_agent: ArchitectAgent) -> None:
        """agent_type is ARCHITECT."""
        assert architect_agent.agent_type == AgentType.ARCHITECT

    def test_architect_extends_base_agent(self, architect_agent: ArchitectAgent) -> None:
        """ArchitectAgent is a subclass of BaseAgent."""
        assert isinstance(architect_agent, BaseAgent)

    def test_architect_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions architecture."""
        assert len(ARCHITECT_SYSTEM_PROMPT) > 0
        assert "architect" in ARCHITECT_SYSTEM_PROMPT.lower()


class TestArchitectReview:
    """ArchitectAgent.review() validates output."""

    async def test_architect_review_passes_with_valid_output(
        self, architect_agent: ArchitectAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "architecture_doc": "System architecture document",
                "component_diagram": {"components": []},
                "data_flow": [],
                "adr_records": [],
            },
        )
        output = await architect_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_architect_review_fails_with_empty_output(
        self, architect_agent: ArchitectAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(is_complete=True, data={})
        output = await architect_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestArchitectPerceive:
    """ArchitectAgent.perceive() extracts context."""

    async def test_architect_perceive_extracts_research_output(
        self, architect_agent: ArchitectAgent, agent_input: AgentInput
    ) -> None:
        """perceive() returns dict containing research_output."""
        result = await architect_agent.perceive(agent_input)
        assert "research_output" in result
        assert "project_requirements" in result
        assert "tech_stack" in result


# ---------------------------------------------------------------------------
# DesignerAgent tests
# ---------------------------------------------------------------------------


class TestDesignerAgentType:
    """DesignerAgent has correct type and inheritance."""

    def test_designer_agent_type(self, designer_agent: DesignerAgent) -> None:
        """agent_type is DESIGNER."""
        assert designer_agent.agent_type == AgentType.DESIGNER

    def test_designer_extends_base_agent(self, designer_agent: DesignerAgent) -> None:
        """DesignerAgent is a subclass of BaseAgent."""
        assert isinstance(designer_agent, BaseAgent)

    def test_designer_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions design."""
        assert len(DESIGNER_SYSTEM_PROMPT) > 0
        assert "designer" in DESIGNER_SYSTEM_PROMPT.lower()


class TestDesignerReview:
    """DesignerAgent.review() validates output."""

    async def test_designer_review_passes_with_valid_output(
        self, designer_agent: DesignerAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "wireframes": [{"page_name": "dashboard"}],
                "component_hierarchy": {"root": "App"},
            },
        )
        output = await designer_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_designer_review_fails_with_empty_output(
        self, designer_agent: DesignerAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(is_complete=True, data={})
        output = await designer_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# TemplateCuratorAgent tests
# ---------------------------------------------------------------------------


class TestTemplateCuratorAgentType:
    """TemplateCuratorAgent has correct type and inheritance."""

    def test_template_agent_type(self, template_agent: TemplateCuratorAgent) -> None:
        """agent_type is TEMPLATE_CURATOR."""
        assert template_agent.agent_type == AgentType.TEMPLATE_CURATOR

    def test_template_extends_base_agent(self, template_agent: TemplateCuratorAgent) -> None:
        """TemplateCuratorAgent is a subclass of BaseAgent."""
        assert isinstance(template_agent, BaseAgent)

    def test_template_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions template."""
        assert len(TEMPLATE_SYSTEM_PROMPT) > 0
        assert "template" in TEMPLATE_SYSTEM_PROMPT.lower()

    def test_template_system_prompt_mentions_shadcn(self) -> None:
        """SYSTEM_PROMPT mentions Shadcn/ui."""
        assert "shadcn" in TEMPLATE_SYSTEM_PROMPT.lower()

    def test_template_system_prompt_mentions_tailwind_ui(self) -> None:
        """SYSTEM_PROMPT mentions Tailwind UI."""
        assert "tailwind ui" in TEMPLATE_SYSTEM_PROMPT.lower()

    def test_template_system_prompt_mentions_material(self) -> None:
        """SYSTEM_PROMPT mentions Material Design."""
        assert "material design" in TEMPLATE_SYSTEM_PROMPT.lower()


class TestTemplateCuratorReview:
    """TemplateCuratorAgent.review() validates output."""

    async def test_template_review_passes_with_valid_output(
        self, template_agent: TemplateCuratorAgent
    ) -> None:
        """review() returns review_passed=True when selected_template present."""
        pra_result = PRAResult(
            is_complete=True,
            data={"selected_template": {"name": "shadcn-ui"}},
        )
        output = await template_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_template_review_fails_with_empty_output(
        self, template_agent: TemplateCuratorAgent
    ) -> None:
        """review() returns review_passed=False when selected_template missing."""
        pra_result = PRAResult(is_complete=True, data={})
        output = await template_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# DatabaseDesignerAgent tests
# ---------------------------------------------------------------------------


class TestDatabaseDesignerAgentType:
    """DatabaseDesignerAgent has correct type and inheritance."""

    def test_database_agent_type(self, database_agent: DatabaseDesignerAgent) -> None:
        """agent_type falls back to ARCHITECT."""
        assert database_agent.agent_type == AgentType.ARCHITECT

    def test_database_extends_base_agent(self, database_agent: DatabaseDesignerAgent) -> None:
        """DatabaseDesignerAgent is a subclass of BaseAgent."""
        assert isinstance(database_agent, BaseAgent)

    def test_database_agent_name(self, database_agent: DatabaseDesignerAgent) -> None:
        """name is 'database_designer'."""
        assert database_agent.name == "database_designer"

    def test_database_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions database."""
        assert len(DB_SYSTEM_PROMPT) > 0
        assert "database" in DB_SYSTEM_PROMPT.lower()


class TestDatabaseDesignerReview:
    """DatabaseDesignerAgent.review() validates output."""

    async def test_database_review_passes_with_valid_output(
        self, database_agent: DatabaseDesignerAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "database_schema": {"tables": []},
                "migrations": [{"id": 1, "description": "init"}],
            },
        )
        output = await database_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_database_review_fails_with_empty_output(
        self, database_agent: DatabaseDesignerAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(is_complete=True, data={})
        output = await database_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# APIDesignerAgent tests
# ---------------------------------------------------------------------------


class TestAPIDesignerAgentType:
    """APIDesignerAgent has correct type and inheritance."""

    def test_api_agent_type(self, api_agent: APIDesignerAgent) -> None:
        """agent_type is API_DESIGNER."""
        assert api_agent.agent_type == AgentType.API_DESIGNER

    def test_api_extends_base_agent(self, api_agent: APIDesignerAgent) -> None:
        """APIDesignerAgent is a subclass of BaseAgent."""
        assert isinstance(api_agent, BaseAgent)

    def test_api_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions API."""
        assert len(API_SYSTEM_PROMPT) > 0
        assert "api" in API_SYSTEM_PROMPT.lower()


class TestAPIDesignerReview:
    """APIDesignerAgent.review() validates output."""

    async def test_api_review_passes_with_valid_output(
        self, api_agent: APIDesignerAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "api_spec": {"openapi": "3.1.0"},
                "endpoint_definitions": [{"method": "GET", "path": "/api/v1/projects"}],
            },
        )
        output = await api_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_api_review_fails_with_empty_output(
        self, api_agent: APIDesignerAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(is_complete=True, data={})
        output = await api_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# Parallel safety: distinct SharedState keys (ARCH-05)
# ---------------------------------------------------------------------------


class TestS3ParallelSafety:
    """All S3 agents write to distinct SharedState keys for parallel execution."""

    async def test_all_s3_agents_write_different_state_keys(
        self,
        architect_agent: ArchitectAgent,
        designer_agent: DesignerAgent,
        template_agent: TemplateCuratorAgent,
        database_agent: DatabaseDesignerAgent,
        api_agent: APIDesignerAgent,
    ) -> None:
        """Each S3 agent writes to a unique state_updates key."""
        valid_results = {
            "architect": PRAResult(
                is_complete=True,
                data={"architecture_doc": "doc", "component_diagram": {}},
            ),
            "designer": PRAResult(
                is_complete=True,
                data={"wireframes": [], "component_hierarchy": {}},
            ),
            "template": PRAResult(
                is_complete=True,
                data={"selected_template": {"name": "shadcn-ui"}},
            ),
            "database": PRAResult(
                is_complete=True,
                data={"database_schema": {}, "migrations": []},
            ),
            "api": PRAResult(
                is_complete=True,
                data={"api_spec": {}, "endpoint_definitions": []},
            ),
        }

        architect_output = await architect_agent.review(valid_results["architect"])
        designer_output = await designer_agent.review(valid_results["designer"])
        template_output = await template_agent.review(valid_results["template"])
        database_output = await database_agent.review(valid_results["database"])
        api_output = await api_agent.review(valid_results["api"])

        keys = {
            frozenset(architect_output.state_updates.keys()),
            frozenset(designer_output.state_updates.keys()),
            frozenset(template_output.state_updates.keys()),
            frozenset(database_output.state_updates.keys()),
            frozenset(api_output.state_updates.keys()),
        }

        # All 5 agents must produce different state_updates keys
        assert len(keys) == 5, (
            f"Expected 5 distinct state_updates key sets, got {len(keys)}: "
            f"architect={list(architect_output.state_updates.keys())}, "
            f"designer={list(designer_output.state_updates.keys())}, "
            f"template={list(template_output.state_updates.keys())}, "
            f"database={list(database_output.state_updates.keys())}, "
            f"api={list(api_output.state_updates.keys())}"
        )

        # Verify specific keys
        assert "architect_output" in architect_output.state_updates
        assert "designer_output" in designer_output.state_updates
        assert "template_output" in template_output.state_updates
        assert "database_output" in database_output.state_updates
        assert "api_designer_output" in api_output.state_updates


# ---------------------------------------------------------------------------
# YAML config tests
# ---------------------------------------------------------------------------


class TestArchitectYAMLConfig:
    """architect.yaml loads and validates."""

    def test_architect_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "architect.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["architect"]["agent_type"] == "ARCHITECT"


class TestDesignerYAMLConfig:
    """designer.yaml loads and validates."""

    def test_designer_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "designer.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["designer"]["agent_type"] == "DESIGNER"


class TestTemplateYAMLConfig:
    """template.yaml loads and validates."""

    def test_template_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "template.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["template"]["agent_type"] == "TEMPLATE_CURATOR"


class TestDatabaseYAMLConfig:
    """database.yaml loads and validates."""

    def test_database_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "database.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["database"]["agent_type"] == "ARCHITECT"


class TestAPIGatewayYAMLConfig:
    """api_gateway.yaml loads and validates."""

    def test_api_gateway_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "api_gateway.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["api_gateway"]["agent_type"] == "API_DESIGNER"
