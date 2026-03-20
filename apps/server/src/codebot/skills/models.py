"""Skill domain models for the skill registry.

Defines the Skill dataclass used by SkillService and SkillCreatorAgent.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SkillStatus(StrEnum):
    """Lifecycle status for a Skill."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"


@dataclass(slots=True, kw_only=True)
class Skill:
    """A reusable code pattern packaged as a skill.

    Attributes:
        id: Unique skill identifier.
        name: Human-readable skill name.
        description: What the skill does.
        version: Semantic version string.
        created_by_agent: Agent type that created this skill.
        target_agents: Agent types that can use this skill.
        code: Parameterized source code for the skill.
        status: Current lifecycle status.
        dependencies: Required external dependencies.
        tags: Searchable tags for discovery.
        input_schema: JSON Schema for skill inputs.
        output_schema: JSON Schema for skill outputs.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    created_by_agent: str = ""
    target_agents: list[str] = field(default_factory=list)
    code: str = ""
    status: SkillStatus = SkillStatus.DRAFT
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
