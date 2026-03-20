"""Root test configuration with shared fixtures.

Provides a Temporal WorkflowEnvironment fixture using the in-memory
time-skipping server so integration tests run without an external
Temporal deployment.  Also provides shared LLM mock fixtures for
unit tests across the input and agent domains.
"""

from __future__ import annotations

import pytest
from codebot.input.models import (
    AcceptanceCriterion,
    ExtractedRequirements,
    FunctionalRequirement,
)
from temporalio.testing import WorkflowEnvironment


@pytest.fixture
async def temporal_env() -> WorkflowEnvironment:  # type: ignore[misc]
    """Yield a Temporal time-skipping test environment.

    The environment uses an embedded Temporal test server with
    time-skipping support so timer-dependent workflows complete
    instantly.  No external Temporal server is required.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env  # type: ignore[misc]


@pytest.fixture
def mock_extracted_requirements() -> ExtractedRequirements:
    """Pre-built ExtractedRequirements for testing across modules.

    Returns a complete requirements object for a "Todo API" project
    with two functional requirements (FR-01 Create todo, FR-02 List todos),
    each with acceptance criteria and confidence=0.95.
    """
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
