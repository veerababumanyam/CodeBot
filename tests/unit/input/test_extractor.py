"""Unit tests for input domain models and RequirementExtractor.

All LLM calls are mocked via the mock_instructor_client fixture.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.input.models import (
    AcceptanceCriterion,
    ExtractedRequirements,
    FunctionalRequirement,
)
from codebot.input.extractor import RequirementExtractor


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------


class TestAcceptanceCriterionModel:
    """AcceptanceCriterion model validates with description and test_strategy."""

    def test_valid_criterion(self) -> None:
        criterion = AcceptanceCriterion(
            description="POST /todos returns 201 with created item",
            test_strategy="integration_test",
        )
        assert criterion.description == "POST /todos returns 201 with created item"
        assert criterion.test_strategy == "integration_test"


class TestFunctionalRequirementModel:
    """FunctionalRequirement model validation."""

    def test_valid_requirement(self) -> None:
        fr = FunctionalRequirement(
            id="FR-01",
            title="Create todo",
            description="User can create a new todo item",
            priority="Must",
            acceptance_criteria=[
                AcceptanceCriterion(
                    description="Returns 201",
                    test_strategy="unit_test",
                )
            ],
            confidence=0.95,
        )
        assert fr.id == "FR-01"
        assert fr.title == "Create todo"
        assert fr.priority == "Must"
        assert fr.confidence == 0.95
        assert len(fr.acceptance_criteria) == 1

    def test_rejects_confidence_below_zero(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            FunctionalRequirement(
                id="FR-01",
                title="Bad",
                description="Bad confidence",
                priority="Must",
                acceptance_criteria=[],
                confidence=-0.1,
            )

    def test_rejects_confidence_above_one(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            FunctionalRequirement(
                id="FR-01",
                title="Bad",
                description="Bad confidence",
                priority="Must",
                acceptance_criteria=[],
                confidence=1.1,
            )


class TestExtractedRequirementsModel:
    """ExtractedRequirements model validates with all fields."""

    def test_valid_requirements(self) -> None:
        reqs = ExtractedRequirements(
            project_name="Todo API",
            project_description="A simple todo API",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-01",
                    title="Create todo",
                    description="User can create a new todo item",
                    priority="Must",
                    acceptance_criteria=[
                        AcceptanceCriterion(
                            description="Returns 201",
                            test_strategy="unit_test",
                        )
                    ],
                    confidence=0.9,
                )
            ],
            non_functional_requirements=["Response time < 200ms"],
            constraints=["Python 3.12+"],
            ambiguities=["What database to use?"],
        )
        assert reqs.project_name == "Todo API"
        assert len(reqs.functional_requirements) == 1
        assert len(reqs.non_functional_requirements) == 1
        assert len(reqs.constraints) == 1
        assert len(reqs.ambiguities) == 1

    def test_ambiguities_defaults_to_empty(self) -> None:
        reqs = ExtractedRequirements(
            project_name="Test",
            project_description="Test project",
            functional_requirements=[],
            non_functional_requirements=[],
            constraints=[],
        )
        assert reqs.ambiguities == []


# ---------------------------------------------------------------------------
# RequirementExtractor tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_extracted_requirements() -> ExtractedRequirements:
    """Pre-built ExtractedRequirements for testing."""
    return ExtractedRequirements(
        project_name="Todo API",
        project_description="A simple todo list API",
        functional_requirements=[
            FunctionalRequirement(
                id="FR-01",
                title="Create todo",
                description="User can create a new todo item with title and description",
                priority="Must",
                acceptance_criteria=[
                    AcceptanceCriterion(
                        description="POST /todos returns 201 with created item",
                        test_strategy="integration_test",
                    )
                ],
                confidence=0.95,
            ),
            FunctionalRequirement(
                id="FR-02",
                title="List todos",
                description="User can list all todo items",
                priority="Must",
                acceptance_criteria=[
                    AcceptanceCriterion(
                        description="GET /todos returns 200 with list of items",
                        test_strategy="integration_test",
                    )
                ],
                confidence=0.95,
            ),
        ],
        non_functional_requirements=["Response time < 200ms"],
        constraints=["Python 3.12+", "FastAPI framework"],
        ambiguities=[],
    )


@pytest.fixture
def mock_instructor_client(
    mock_extracted_requirements: ExtractedRequirements,
) -> MagicMock:
    """Patch instructor.from_litellm to return a mock client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_extracted_requirements
    )

    with patch("codebot.input.extractor.instructor") as mock_instructor:
        mock_instructor.from_litellm.return_value = mock_client
        yield mock_client


class TestRequirementExtractorExtract:
    """RequirementExtractor.extract() returns ExtractedRequirements."""

    async def test_natural_language_input(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extract returns ExtractedRequirements from natural language input."""
        extractor = RequirementExtractor()
        result = await extractor.extract(
            "Build me a todo list API with create and list endpoints"
        )
        assert isinstance(result, ExtractedRequirements)
        assert result.project_name == "Todo API"
        assert len(result.functional_requirements) == 2
        mock_instructor_client.chat.completions.create.assert_awaited_once()

    async def test_json_input(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extract returns ExtractedRequirements from JSON input."""
        extractor = RequirementExtractor()
        result = await extractor.extract('{"project": "todo api", "features": ["create", "list"]}')
        assert isinstance(result, ExtractedRequirements)

    async def test_yaml_input(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extract returns ExtractedRequirements from YAML input."""
        extractor = RequirementExtractor()
        result = await extractor.extract("---\nproject: todo api\nfeatures:\n  - create\n  - list")
        assert isinstance(result, ExtractedRequirements)

    async def test_markdown_input(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extract returns ExtractedRequirements from Markdown input."""
        extractor = RequirementExtractor()
        result = await extractor.extract("# Todo API\n\n## Features\n- Create todos\n- List todos")
        assert isinstance(result, ExtractedRequirements)

    async def test_structured_input_formats(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extract handles all structured input formats."""
        extractor = RequirementExtractor()
        for input_text in [
            '{"project": "test"}',
            "---\nproject: test\n",
            "# Test\n## Requirements\n- Feature A",
        ]:
            result = await extractor.extract(input_text)
            assert isinstance(result, ExtractedRequirements)

    async def test_extraction_completeness(
        self,
        mock_instructor_client: MagicMock,
        mock_extracted_requirements: ExtractedRequirements,
    ) -> None:
        """Extracted requirements have at least one FR with non-empty acceptance_criteria."""
        extractor = RequirementExtractor()
        result = await extractor.extract("Build me a todo API")
        assert len(result.functional_requirements) >= 1
        for fr in result.functional_requirements:
            assert len(fr.acceptance_criteria) > 0


class TestRequirementExtractorDetectFormat:
    """RequirementExtractor._detect_format() detects input types."""

    def test_detect_natural_language(self) -> None:
        assert RequirementExtractor._detect_format("Build me a todo API") == "natural_language"

    def test_detect_json(self) -> None:
        assert RequirementExtractor._detect_format('{"project": "test"}') == "json"

    def test_detect_yaml(self) -> None:
        assert RequirementExtractor._detect_format("---\nproject: test") == "yaml"
        assert RequirementExtractor._detect_format("project:\n  name: test") == "yaml"

    def test_detect_markdown(self) -> None:
        assert RequirementExtractor._detect_format("# Project Title") == "markdown"
        assert RequirementExtractor._detect_format("Some text\n## Requirements") == "markdown"
