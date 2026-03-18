"""Shared fixtures for context management unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def sample_l0_context() -> dict[str, object]:
    """Return sample L0 context data for testing."""
    return {
        "project_name": "TestProject",
        "project_description": "A test project for unit tests",
        "tech_stack": ["python", "fastapi", "react"],
        "conventions": "Use snake_case for Python. Use PascalCase for classes.",
        "pipeline_phase": "IMPLEMENTATION",
        "agent_system_prompt": "You are a helpful coding assistant.",
        "constraints": ["No external API calls in tests"],
    }


@pytest.fixture()
def sample_l1_context() -> dict[str, object]:
    """Return sample L1 context data for testing."""
    return {
        "phase_requirements": "Implement the authentication module with JWT tokens.",
        "related_files": ["src/auth.py", "src/models/user.py"],
        "architecture_decisions": "Use jose for JWT, bcrypt for hashing.",
        "upstream_outputs": {"brainstorm": "Use OAuth2 flow"},
    }


@pytest.fixture()
def sample_code_content() -> str:
    """Return a multi-line Python code string (~100 tokens) for testing."""
    return '''\
import asyncio
from dataclasses import dataclass

@dataclass(slots=True, kw_only=True)
class UserService:
    """Service for managing user operations."""

    db_url: str
    cache_ttl: int = 300

    async def get_user(self, user_id: str) -> dict:
        """Fetch a user by their unique identifier."""
        await asyncio.sleep(0)  # simulate async I/O
        return {"id": user_id, "name": "Test User", "email": "test@example.com"}

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user record."""
        return {"id": "new-uuid", "name": name, "email": email}
'''
