"""Unit tests for ThreeTierLoader L0/L1 context loading.

Tests cover:
- L0 loading from .codebot/context/L0/ filesystem
- L0 graceful defaults when files are missing
- L0 token count capping at ~2500 tokens
- L1 loading with phase-specific requirements
- L1 role-based file selection (BACKEND_DEV, FRONTEND_DEV, TESTER)
- L1 graceful defaults when phase directory is missing
- L1 default role fallback for unknown agent roles
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tiktoken

from codebot.context.models import L0Context, L1Context
from codebot.context.tiers import ThreeTierLoader


@pytest.fixture()
def l0_project_dir(tmp_path: Path) -> Path:
    """Create a project directory with L0 context files."""
    l0_dir = tmp_path / ".codebot" / "context" / "L0"
    l0_dir.mkdir(parents=True)

    (l0_dir / "summary.md").write_text(
        "# TestProject\n\n"
        "A test project for validating the context management system.\n\n"
        "## Tech Stack\n"
        "- Python 3.12\n"
        "- FastAPI\n"
        "- React\n"
        "- PostgreSQL\n"
    )

    (l0_dir / "conventions.md").write_text(
        "Use snake_case for Python functions and variables.\n"
        "Use PascalCase for classes.\n"
        "Use Google-style docstrings.\n"
        "Format with ruff, lint with ruff check.\n"
    )

    (l0_dir / "constraints.md").write_text(
        "No external API calls in unit tests.\n"
        "All async functions must use asyncio.TaskGroup.\n"
        "Minimum test coverage: 80% line, 70% branch.\n"
    )

    return tmp_path


@pytest.fixture()
def l1_project_dir(tmp_path: Path) -> Path:
    """Create a project directory with L1 context files."""
    l1_dir = tmp_path / ".codebot" / "context" / "L1"
    l1_dir.mkdir(parents=True)

    # Phase requirements
    phases_dir = l1_dir / "phases" / "IMPLEMENTATION"
    phases_dir.mkdir(parents=True)
    (phases_dir / "requirements.md").write_text(
        "# Implementation Phase Requirements\n\n"
        "1. Implement all API endpoints defined in the API spec.\n"
        "2. Write unit tests for each endpoint.\n"
        "3. Ensure database migrations are created.\n"
    )

    # Architecture decisions
    arch_dir = l1_dir / "architecture"
    arch_dir.mkdir(parents=True)
    (arch_dir / "decisions.md").write_text(
        "# Architecture Decisions\n\n"
        "- ADR-001: Use FastAPI for the backend.\n"
        "- ADR-002: PostgreSQL for persistent storage.\n"
    )

    # Schema files
    schemas_dir = l1_dir / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "db.md").write_text(
        "# Database Schema\n\n"
        "## users table\n"
        "- id: UUID primary key\n"
        "- email: VARCHAR unique\n"
        "- name: VARCHAR\n"
    )

    # API spec files
    api_dir = l1_dir / "api-specs"
    api_dir.mkdir(parents=True)
    (api_dir / "auth.md").write_text(
        "# Auth API\n\n"
        "POST /api/auth/login\n"
        "POST /api/auth/register\n"
    )

    # Design files
    designs_dir = l1_dir / "designs"
    designs_dir.mkdir(parents=True)
    (designs_dir / "ui.md").write_text(
        "# UI Design\n\n"
        "Dashboard layout with sidebar navigation.\n"
    )

    return tmp_path


class TestThreeTierLoaderL0:
    """Tests for L0 context loading."""

    async def test_load_l0_returns_l0_context(self, l0_project_dir: Path) -> None:
        """load_l0() should return an L0Context with populated fields."""
        loader = ThreeTierLoader(project_root=l0_project_dir)
        result = await loader.load_l0(
            agent_system_prompt="You are a coding assistant.",
            pipeline_phase="IMPLEMENTATION",
        )
        assert isinstance(result, L0Context)
        assert result.project_name == "TestProject"
        assert "test project" in result.project_description.lower()
        assert len(result.tech_stack) >= 3
        assert "Python 3.12" in result.tech_stack
        assert result.conventions != ""
        assert result.agent_system_prompt == "You are a coding assistant."
        assert result.pipeline_phase == "IMPLEMENTATION"

    async def test_load_l0_graceful_when_files_missing(
        self, tmp_path: Path
    ) -> None:
        """load_l0() should return L0Context with defaults when files are missing."""
        # Only create summary.md, skip conventions and constraints
        l0_dir = tmp_path / ".codebot" / "context" / "L0"
        l0_dir.mkdir(parents=True)
        (l0_dir / "summary.md").write_text(
            "# MinimalProject\n\nA minimal project.\n"
        )

        loader = ThreeTierLoader(project_root=tmp_path)
        result = await loader.load_l0()
        assert isinstance(result, L0Context)
        assert result.project_name == "MinimalProject"
        # conventions and constraints should have empty defaults
        assert result.conventions == ""
        assert result.constraints == []

    async def test_load_l0_token_count_under_2500(
        self, l0_project_dir: Path
    ) -> None:
        """L0 context token count should be under 2500 tokens."""
        loader = ThreeTierLoader(project_root=l0_project_dir)
        result = await loader.load_l0(
            agent_system_prompt="You are a coding assistant.",
            pipeline_phase="IMPLEMENTATION",
        )
        # Count total tokens across all fields
        encoder = tiktoken.get_encoding("cl100k_base")
        combined = (
            f"{result.project_name}\n"
            f"{result.project_description}\n"
            f"{' '.join(result.tech_stack)}\n"
            f"{result.conventions}\n"
            f"{result.agent_system_prompt}\n"
            f"{result.pipeline_phase}\n"
            f"{' '.join(result.constraints)}\n"
        )
        token_count = len(encoder.encode(combined))
        assert token_count < 2500, f"L0 context is {token_count} tokens, exceeds 2500"

    async def test_load_l0_completely_missing_dir(self, tmp_path: Path) -> None:
        """load_l0() should return defaults when L0 directory does not exist at all."""
        loader = ThreeTierLoader(project_root=tmp_path)
        result = await loader.load_l0()
        assert isinstance(result, L0Context)
        assert result.project_name == ""
        assert result.tech_stack == []


class TestThreeTierLoaderL1:
    """Tests for L1 context loading."""

    async def test_load_l1_returns_phase_requirements(
        self, l1_project_dir: Path
    ) -> None:
        """load_l1() should return L1Context with phase requirements."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="IMPLEMENTATION", agent_role="BACKEND_DEV"
        )
        assert isinstance(result, L1Context)
        assert result.phase_requirements != ""
        assert "API endpoints" in result.phase_requirements

    async def test_load_l1_role_specific_files_backend_dev(
        self, l1_project_dir: Path
    ) -> None:
        """BACKEND_DEV role should load schemas and api-specs."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="IMPLEMENTATION", agent_role="BACKEND_DEV"
        )
        # BACKEND_DEV should have schemas and api-specs in related_files
        file_names = [Path(f).name for f in result.related_files]
        assert "db.md" in file_names, f"schemas/db.md not loaded for BACKEND_DEV. Files: {result.related_files}"
        assert "auth.md" in file_names, f"api-specs/auth.md not loaded for BACKEND_DEV. Files: {result.related_files}"

    async def test_load_l1_role_specific_files_frontend_dev(
        self, l1_project_dir: Path
    ) -> None:
        """FRONTEND_DEV role should load api-specs and designs."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="IMPLEMENTATION", agent_role="FRONTEND_DEV"
        )
        file_names = [Path(f).name for f in result.related_files]
        assert "auth.md" in file_names, f"api-specs not loaded for FRONTEND_DEV. Files: {result.related_files}"
        assert "ui.md" in file_names, f"designs not loaded for FRONTEND_DEV. Files: {result.related_files}"

    async def test_load_l1_empty_when_phase_missing(
        self, l1_project_dir: Path
    ) -> None:
        """load_l1() should return empty L1Context when phase directory is missing."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="NONEXISTENT_PHASE", agent_role="BACKEND_DEV"
        )
        assert isinstance(result, L1Context)
        assert result.phase_requirements == ""

    async def test_load_l1_default_role_fallback(
        self, l1_project_dir: Path
    ) -> None:
        """Unknown roles should fall back to DEFAULT file patterns."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="IMPLEMENTATION", agent_role="UNKNOWN_AGENT_ROLE"
        )
        assert isinstance(result, L1Context)
        # DEFAULT pattern only includes architecture/decisions.md
        file_names = [Path(f).name for f in result.related_files]
        assert "decisions.md" in file_names, (
            f"DEFAULT pattern should load architecture/decisions.md. Files: {result.related_files}"
        )

    async def test_load_l1_tester_role_includes_schemas(
        self, l1_project_dir: Path
    ) -> None:
        """TESTER role should include schemas and api-specs."""
        loader = ThreeTierLoader(project_root=l1_project_dir)
        result = await loader.load_l1(
            phase="IMPLEMENTATION", agent_role="TESTER"
        )
        file_names = [Path(f).name for f in result.related_files]
        assert "db.md" in file_names, f"schemas not loaded for TESTER. Files: {result.related_files}"
        assert "auth.md" in file_names, f"api-specs not loaded for TESTER. Files: {result.related_files}"
