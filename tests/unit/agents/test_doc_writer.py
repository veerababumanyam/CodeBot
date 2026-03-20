"""Unit tests for DocumentationWriterAgent.

Validates agent type, BaseAgent inheritance, system prompt content,
review logic, and YAML config loading.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml

from agent_sdk.agents.base import AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.doc_writer import SYSTEM_PROMPT, DocumentationWriterAgent


class TestDocumentationWriterAgent:
    """Tests for DocumentationWriterAgent."""

    def test_agent_type_is_doc_writer(self) -> None:
        """Agent type must be AgentType.DOC_WRITER."""
        agent = DocumentationWriterAgent()
        assert agent.agent_type == AgentType.DOC_WRITER

    def test_extends_base_agent(self) -> None:
        """DocumentationWriterAgent must extend BaseAgent."""
        agent = DocumentationWriterAgent()
        assert isinstance(agent, BaseAgent)

    def test_system_prompt_mentions_api_docs(self) -> None:
        """System prompt must mention API documentation (DOCS-01)."""
        assert "API" in SYSTEM_PROMPT

    def test_system_prompt_mentions_adr(self) -> None:
        """System prompt must mention Architecture Decision Records (DOCS-03)."""
        assert "ADR" in SYSTEM_PROMPT or "architecture decision" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_deployment_guide(self) -> None:
        """System prompt must mention deployment guides (DOCS-04)."""
        assert "deployment" in SYSTEM_PROMPT.lower()

    @pytest.mark.asyncio
    async def test_review_passes_with_api_docs_and_guide(self) -> None:
        """Review passes when api_docs and user_guide are present."""
        agent = DocumentationWriterAgent()
        result = PRAResult(
            is_complete=True,
            data={
                "api_docs": {"endpoints": []},
                "user_guide": {"getting_started": "..."},
                "setup_instructions": "",
                "adr_records": [],
                "deployment_guide": {},
                "generated_files": [],
            },
        )
        output: AgentOutput = await agent.review(result)
        assert output.review_passed is True
        assert "doc_writer_output" in output.state_updates

    @pytest.mark.asyncio
    async def test_review_fails_without_api_docs(self) -> None:
        """Review fails when api_docs is missing."""
        agent = DocumentationWriterAgent()
        result = PRAResult(
            is_complete=True,
            data={
                "user_guide": {"getting_started": "..."},
            },
        )
        output: AgentOutput = await agent.review(result)
        assert output.review_passed is False

    @pytest.mark.asyncio
    async def test_review_fails_without_user_guide(self) -> None:
        """Review fails when user_guide is missing."""
        agent = DocumentationWriterAgent()
        result = PRAResult(
            is_complete=True,
            data={
                "api_docs": {"endpoints": []},
            },
        )
        output: AgentOutput = await agent.review(result)
        assert output.review_passed is False

    def test_yaml_config_loads(self) -> None:
        """YAML config file must load and contain correct agent_type."""
        config_path = Path("configs/agents/doc_writer.yaml")
        assert config_path.exists(), f"Config file not found: {config_path}"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert "doc_writer" in config
        assert config["doc_writer"]["agent_type"] == "DOC_WRITER"

    def test_tools_include_expected(self) -> None:
        """Agent must have documentation-related tools."""
        agent = DocumentationWriterAgent()
        assert "openapi_renderer" in agent.tools
        assert "adr_formatter" in agent.tools
        assert "deployment_guide_generator" in agent.tools

    def test_agent_has_unique_id(self) -> None:
        """Each agent instance must have a unique UUID."""
        a1 = DocumentationWriterAgent()
        a2 = DocumentationWriterAgent()
        assert a1.agent_id != a2.agent_id
        assert isinstance(a1.agent_id, uuid.UUID)
