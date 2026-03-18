"""Unit tests for VectorStoreBackend implementations."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from codebot.context.vector_store import LanceDBBackend, VectorResult


def _random_embedding(dim: int = 384) -> list[float]:
    """Generate a random embedding vector for testing."""
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]


class TestVectorResult:
    """Tests for the VectorResult model."""

    def test_vector_result_model(self) -> None:
        result = VectorResult(
            id="test-1",
            content="def hello(): pass",
            score=0.95,
            metadata={"file_path": "app.py", "symbol_kind": "function"},
        )
        assert result.id == "test-1"
        assert result.content == "def hello(): pass"
        assert result.score == 0.95
        assert result.metadata == {"file_path": "app.py", "symbol_kind": "function"}

    def test_vector_result_empty_metadata(self) -> None:
        result = VectorResult(id="test-2", content="text", score=0.5, metadata={})
        assert result.metadata == {}


class TestLanceDBBackend:
    """Tests for the LanceDB vector store backend."""

    @pytest.mark.asyncio
    async def test_lancedb_backend_init(self, tmp_path: Path) -> None:
        backend = LanceDBBackend(persist_dir=str(tmp_path / "lancedb"))
        assert backend is not None

    @pytest.mark.asyncio
    async def test_lancedb_upsert_and_query(self, tmp_path: Path) -> None:
        backend = LanceDBBackend(persist_dir=str(tmp_path / "lancedb"))

        # Upsert 3 items
        for i in range(3):
            await backend.upsert(
                id=f"item-{i}",
                content=f"def function_{i}(): pass",
                embedding=_random_embedding(),
                metadata={
                    "file_path": f"module_{i}.py",
                    "symbol_name": f"function_{i}",
                    "symbol_kind": "function",
                    "project_id": "proj-1",
                    "line_start": i * 10 + 1,
                    "line_end": i * 10 + 5,
                },
            )

        # Query
        results = await backend.query(
            query_embedding=_random_embedding(),
            top_k=5,
        )
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, VectorResult) for r in results)

    @pytest.mark.asyncio
    async def test_lancedb_delete(self, tmp_path: Path) -> None:
        backend = LanceDBBackend(persist_dir=str(tmp_path / "lancedb"))

        # Upsert an item
        embedding = _random_embedding()
        await backend.upsert(
            id="delete-me",
            content="def remove_this(): pass",
            embedding=embedding,
            metadata={
                "file_path": "temp.py",
                "symbol_name": "remove_this",
                "symbol_kind": "function",
                "project_id": "proj-1",
                "line_start": 1,
                "line_end": 2,
            },
        )

        # Delete it
        await backend.delete(ids=["delete-me"])

        # Query should return empty or not contain deleted item
        results = await backend.query(query_embedding=embedding, top_k=5)
        result_ids = [r.id for r in results]
        assert "delete-me" not in result_ids

    @pytest.mark.asyncio
    async def test_lancedb_query_respects_top_k(self, tmp_path: Path) -> None:
        backend = LanceDBBackend(persist_dir=str(tmp_path / "lancedb"))

        # Upsert 5 items
        for i in range(5):
            await backend.upsert(
                id=f"topk-{i}",
                content=f"content {i}",
                embedding=_random_embedding(),
                metadata={
                    "file_path": f"file_{i}.py",
                    "symbol_name": f"sym_{i}",
                    "symbol_kind": "function",
                    "project_id": "proj-1",
                    "line_start": 1,
                    "line_end": 2,
                },
            )

        results = await backend.query(query_embedding=_random_embedding(), top_k=2)
        assert len(results) <= 2
