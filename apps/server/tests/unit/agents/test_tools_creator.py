"""Tests for ToolsCreatorAgent -- full implementation (Phase 11).

Verifies the PRA cognitive cycle for generating custom tools and MCP
server configurations, including ToolService integration and event bus publishing.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType


@pytest.fixture
def mock_tool_service() -> AsyncMock:
    """Mock ToolService with create_tool stub."""
    return AsyncMock()


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock EventBus with publish stub."""
    return AsyncMock()


@pytest.fixture
def agent() -> Any:
    """Create a ToolsCreatorAgent instance."""
    from codebot.agents.tools_creator_agent import ToolsCreatorAgent

    return ToolsCreatorAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput for testing."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={},
        context_tiers={},
    )


class TestToolsCreatorAgent:
    """Tests for ToolsCreatorAgent conventions and PRA cycle."""

    def test_agent_type(self, agent: Any) -> None:
        """Agent type must be TOOL_BUILDER (existing enum value)."""
        assert agent.agent_type == AgentType.TOOL_BUILDER

    def test_dataclass_conventions(self, agent: Any) -> None:
        """Verify the agent follows @dataclass(slots=True, kw_only=True) conventions."""
        assert hasattr(agent, "__slots__")
        assert agent.agent_type == AgentType.TOOL_BUILDER

    def test_extends_base_agent(self, agent: Any) -> None:
        """Agent must extend BaseAgent."""
        assert isinstance(agent, BaseAgent)

    def test_has_name_field(self, agent: Any) -> None:
        """Agent must have a human-readable name."""
        assert agent.name == "tools_creator"

    async def test_perceive_extracts_tool_requests(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive extracts tool_requests, existing_tools from shared_state."""
        agent_input.shared_state = {
            "tool_requests": [{"desc": "GitHub PR fetcher"}],
            "existing_tools": ["file_edit"],
        }
        result = await agent.perceive(agent_input)
        assert len(result["tool_requests"]) == 1
        assert result["existing_tools"] == ["file_edit"]

    async def test_perceive_handles_missing_keys(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive returns empty defaults when keys are missing."""
        agent_input.shared_state = {}
        result = await agent.perceive(agent_input)
        assert result["tool_requests"] == []
        assert result["existing_tools"] == []

    async def test_reason_builds_tool_design_plan(self, agent: Any) -> None:
        """Reason builds a tool design plan."""
        context = {
            "tool_requests": [{"desc": "fetch PRs"}],
            "existing_tools": [],
            "project_context": {},
        }
        plan = await agent.reason(context)
        assert "tool_specs" in plan
        assert "perception" in plan

    async def test_act_creates_tool_and_mcp_config(
        self,
        agent: Any,
        mock_tool_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act creates tools via ToolService and generates MCP config."""
        from codebot.agents.tools_creator_agent import ToolSpec

        agent.set_services(tool_service=mock_tool_service, event_bus=mock_event_bus)

        spec = ToolSpec(
            name="github_pr_fetch",
            description="Fetches open PRs from GitHub",
            parameters={
                "type": "object",
                "properties": {"repo": {"type": "string"}, "state": {"type": "string"}},
                "required": ["repo"],
            },
            implementation="async def execute(repo, state='open'): ...",
            tags=["github", "pr"],
        )
        plan = {"tool_specs": [spec]}
        result = await agent.act(plan)
        assert result.is_complete
        assert "github_pr_fetch" in result.data["created_tools"]
        assert "mcpServers" in result.data["mcp_config"]
        mcp_tools = result.data["mcp_config"]["mcpServers"]["codebot-custom-tools"]["tools"]
        assert mcp_tools[0]["name"] == "github_pr_fetch"
        mock_tool_service.create_tool.assert_called_once()
        mock_event_bus.publish.assert_called_once_with(
            "tool.created",
            {"name": "github_pr_fetch", "version": "1.0.0", "created_by": "tools_creator"},
        )

    async def test_act_rejects_invalid_schema(
        self,
        agent: Any,
        mock_tool_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act rejects tools with invalid parameter schemas."""
        from codebot.agents.tools_creator_agent import ToolSpec

        agent.set_services(tool_service=mock_tool_service, event_bus=mock_event_bus)

        spec = ToolSpec(
            name="bad_tool",
            description="Bad",
            parameters={"invalid": True},
            implementation="",
        )
        plan = {"tool_specs": [spec]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["errors"]) > 0
        assert "Invalid parameter schema" in result.data["errors"][0]

    async def test_act_with_empty_specs(
        self,
        agent: Any,
        mock_tool_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act with empty tool specs returns success."""
        agent.set_services(tool_service=mock_tool_service, event_bus=mock_event_bus)
        result = await agent.act({"tool_specs": []})
        assert result.is_complete
        assert result.data["created_tools"] == []
        assert "mcpServers" in result.data["mcp_config"]

    async def test_act_handles_service_error(
        self,
        agent: Any,
        mock_tool_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act handles ToolService errors gracefully."""
        from codebot.agents.tools_creator_agent import ToolSpec

        mock_tool_service.create_tool.side_effect = RuntimeError("Registry error")
        agent.set_services(tool_service=mock_tool_service, event_bus=mock_event_bus)

        spec = ToolSpec(
            name="failing",
            description="Fails",
            parameters={"type": "object"},
            implementation="",
        )
        plan = {"tool_specs": [spec]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["errors"]) > 0
        assert "Registry error" in result.data["errors"][0]

    def test_generate_mcp_config(self, agent: Any) -> None:
        """generate_mcp_config produces valid MCP server config."""
        from codebot.agents.tools_creator_agent import ToolSpec

        specs = [
            ToolSpec(
                name="t1",
                description="Tool 1",
                parameters={"type": "object"},
                implementation="",
            ),
            ToolSpec(
                name="t2",
                description="Tool 2",
                parameters={"type": "object"},
                implementation="",
            ),
        ]
        config = agent.generate_mcp_config(specs)
        assert "mcpServers" in config
        tools = config["mcpServers"]["codebot-custom-tools"]["tools"]
        assert len(tools) == 2
        assert tools[0]["name"] == "t1"
        assert tools[1]["name"] == "t2"

    async def test_review_validates_output(self, agent: Any) -> None:
        """Review validates and formats the PRA output."""
        pra_result = PRAResult(
            is_complete=True,
            data={"created_tools": ["t1"], "mcp_config": {}, "errors": []},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed
        assert "tools_creator_output" in output.state_updates

    def test_build_system_prompt(self, agent: Any) -> None:
        """Agent has a system prompt."""
        prompt = agent.build_system_prompt()
        assert "Tools Creator" in prompt
        assert len(prompt) > 50
