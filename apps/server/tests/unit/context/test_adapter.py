"""Unit tests for ContextAdapter: full context assembly pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_sdk.models.enums import TaskStatus
from agent_sdk.models.task import TaskSchema
from codebot.context.adapter import ContextAdapter
from codebot.context.compressor import ContextCompressor
from codebot.context.models import (
    AgentContext,
    L0Context,
    L1Context,
    Priority,
)
from codebot.context.vector_store import VectorResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_loader() -> AsyncMock:
    """Create a mock ThreeTierLoader."""
    loader = AsyncMock()
    loader.load_l0.return_value = L0Context(
        project_name="TestProject",
        project_description="A test project for unit tests",
        tech_stack=["python", "fastapi", "react"],
        conventions="Use ruff format. Use snake_case.",
        pipeline_phase="IMPLEMENTATION",
        agent_system_prompt="You are a helpful coding assistant.",
        constraints=["No external API calls in tests"],
    )
    loader.load_l1.return_value = L1Context(
        phase_requirements="Build auth system with JWT tokens",
        related_files=["src/auth.py", "src/models/user.py"],
        architecture_decisions="Use jose for JWT, bcrypt for hashing.",
    )
    return loader


@pytest.fixture()
def mock_vector_store() -> AsyncMock:
    """Create a mock VectorStoreBackend."""
    vs = AsyncMock()
    vs.query.return_value = [
        VectorResult(
            id="v1",
            content="relevant code snippet from vector store",
            score=0.9,
            metadata={"file_path": "src/auth.py"},
        ),
    ]
    return vs


@pytest.fixture()
def mock_compressor() -> AsyncMock:
    """Create a mock ContextCompressor."""
    comp = AsyncMock(spec=ContextCompressor)
    return comp


@pytest.fixture()
def sample_task() -> TaskSchema:
    """Create a sample TaskSchema for testing."""
    return TaskSchema(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        phase_id=uuid.uuid4(),
        title="Build Login Endpoint",
        description="Build login endpoint with JWT authentication",
        status=TaskStatus.PENDING,
        priority=1,
        assigned_agent_type="BACKEND_DEV",
        dependencies=[],
        input_context={},
        created_at=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestContextAdapter:
    """Tests for the ContextAdapter context assembly pipeline."""

    async def test_build_context_includes_l0(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """L0 content should be present in the assembled context."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(
            sample_task,
            agent_system_prompt="You are a helpful coding assistant.",
            pipeline_phase="IMPLEMENTATION",
        )

        text = context.to_text()
        assert "TestProject" in text

    async def test_l0_has_critical_priority(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """L0 context should be added with CRITICAL priority."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(sample_task)

        # First item should be L0 with CRITICAL priority
        items = context.items
        assert len(items) > 0
        assert items[0].priority == Priority.CRITICAL
        assert items[0].source == "l0"

    async def test_task_added_as_high_priority(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """Task description should be added with HIGH priority."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(sample_task)

        text = context.to_text()
        assert "Build login endpoint with JWT authentication" in text

        # Task item should have HIGH priority
        task_items = [i for i in context.items if i.source == "task"]
        assert len(task_items) == 1
        assert task_items[0].priority == Priority.HIGH

    async def test_l1_added_as_medium_priority(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """L1 content should be added with MEDIUM priority."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(sample_task)

        text = context.to_text()
        assert "Build auth system with JWT tokens" in text

        # L1 items should have MEDIUM priority
        l1_items = [
            i for i in context.items if i.source.startswith("l1_")
        ]
        assert len(l1_items) > 0
        for item in l1_items:
            assert item.priority == Priority.MEDIUM

    async def test_l2_added_as_low_priority(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """L2 (vector store) results should be added with LOW priority."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(sample_task)

        text = context.to_text()
        assert "relevant code snippet from vector store" in text

        # L2 items should have LOW priority
        l2_items = [
            i for i in context.items if i.source.startswith("l2_")
        ]
        assert len(l2_items) > 0
        for item in l2_items:
            assert item.priority == Priority.LOW

    async def test_context_within_budget(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """Returned context should be within its token budget."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=mock_vector_store,
        )

        context = await adapter.build_context(sample_task)

        assert not context.is_over_budget()

    async def test_no_vector_store_graceful(
        self,
        mock_loader: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """Adapter should work without a vector store (graceful degradation)."""
        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            # No vector_store provided
        )

        context = await adapter.build_context(sample_task)

        # Should still contain L0 and L1 content
        text = context.to_text()
        assert "TestProject" in text
        assert "Build auth system with JWT tokens" in text

        # No L2 items
        l2_items = [
            i for i in context.items if i.source.startswith("l2_")
        ]
        assert l2_items == []

    async def test_compressor_called_when_over_budget(
        self,
        mock_loader: AsyncMock,
        mock_vector_store: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """Compressor should be called when context exceeds budget."""
        mock_comp = AsyncMock(spec=ContextCompressor)

        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=10,  # Very small budget to force over-budget
            loader=mock_loader,
            compressor=mock_comp,
            vector_store=mock_vector_store,
        )

        await adapter.build_context(sample_task)

        # Compressor.compress should have been called
        mock_comp.compress.assert_called_once()

    async def test_vector_store_error_handled(
        self,
        mock_loader: AsyncMock,
        mock_compressor: AsyncMock,
        sample_task: TaskSchema,
    ) -> None:
        """Vector store errors should be caught, not propagated."""
        failing_vs = AsyncMock()
        failing_vs.query.side_effect = RuntimeError("Connection refused")

        adapter = ContextAdapter(
            agent_role="BACKEND_DEV",
            token_budget=5000,
            loader=mock_loader,
            compressor=mock_compressor,
            vector_store=failing_vs,
        )

        # Should not raise
        context = await adapter.build_context(sample_task)

        # Should still have L0 and task content
        text = context.to_text()
        assert "TestProject" in text
