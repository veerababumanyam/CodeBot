"""Skill service for managing the skill registry.

Provides create, activate, and lookup operations for Skill objects.
"""

from __future__ import annotations

import uuid

from codebot.skills.models import Skill, SkillStatus


class SkillService:
    """Service layer for skill lifecycle management.

    In production, this wraps a database repository. Currently provides
    an in-memory implementation for agent integration.
    """

    def __init__(self) -> None:
        """Initialize with empty in-memory store."""
        self._skills: dict[uuid.UUID, Skill] = {}

    async def create_skill(self, skill: Skill) -> Skill:
        """Register a new skill in the registry.

        Args:
            skill: The Skill object to register.

        Returns:
            The registered Skill (same object, stored internally).

        Raises:
            ValueError: If a skill with the same name already exists.
        """
        for existing in self._skills.values():
            if existing.name == skill.name:
                msg = f"Skill with name '{skill.name}' already exists"
                raise ValueError(msg)
        self._skills[skill.id] = skill
        return skill

    async def activate_skill(self, skill_id: uuid.UUID) -> Skill:
        """Activate a skill, making it available for use.

        Args:
            skill_id: The UUID of the skill to activate.

        Returns:
            The activated Skill.

        Raises:
            KeyError: If skill_id is not found.
        """
        skill = self._skills[skill_id]
        skill.status = SkillStatus.ACTIVE
        return skill
