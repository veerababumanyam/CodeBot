"""Pydantic v2 models for extracted requirements.

Defines the structured output schema for the NLP requirement extraction
pipeline.  These models are used by ``RequirementExtractor`` (via instructor)
to guarantee validated, typed output from LLM calls.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AcceptanceCriterion(BaseModel):
    """A single testable acceptance criterion for a functional requirement.

    Attributes:
        description: What must be true for this criterion to pass.
        test_strategy: How to verify -- unit_test, integration_test, or manual.
    """

    description: str = Field(description="What must be true for this criterion to pass")
    test_strategy: str = Field(
        description="How to verify: unit_test, integration_test, or manual"
    )


class FunctionalRequirement(BaseModel):
    """A single functional requirement extracted from user input.

    Attributes:
        id: Short identifier like FR-01.
        title: Brief requirement title.
        description: Detailed requirement description.
        priority: MoSCoW priority (Must/Should/Could/Won't).
        acceptance_criteria: Testable criteria for this requirement.
        confidence: Extraction confidence score between 0.0 and 1.0.
    """

    id: str = Field(description="Short identifier like FR-01")
    title: str = Field(description="Brief requirement title")
    description: str = Field(description="Detailed requirement description")
    priority: str = Field(description="Must/Should/Could/Won't (MoSCoW)")
    acceptance_criteria: list[AcceptanceCriterion]
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence 0-1")


class NonFunctionalRequirement(BaseModel):
    """A non-functional requirement (performance, security, scalability, etc.).

    Attributes:
        description: What the NFR requires.
        category: Category such as performance, security, scalability.
    """

    description: str = Field(description="What the NFR requires")
    category: str = Field(default="general", description="NFR category")


class ExtractedRequirements(BaseModel):
    """Complete structured output from the requirement extraction pipeline.

    Attributes:
        project_name: Name of the project being described.
        project_description: High-level summary of the project.
        functional_requirements: List of extracted functional requirements.
        non_functional_requirements: List of NFR descriptions.
        constraints: Technical or business constraints.
        ambiguities: Items that are unclear and may need clarification.
    """

    project_name: str
    project_description: str
    functional_requirements: list[FunctionalRequirement]
    non_functional_requirements: list[str]
    constraints: list[str]
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Items that are unclear and may need clarification",
    )
