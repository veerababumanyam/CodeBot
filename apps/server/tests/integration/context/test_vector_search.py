"""Integration tests for LanceDB vector search.

Uses a real embedded LanceDB instance (temp directory) to verify
end-to-end upsert, search, filter, and delete behaviour.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from codebot.context.vector_store import LanceDBBackend, VectorResult


def _random_embedding(dim: int = 384) -> list[float]:
    """Generate a random embedding vector for testing."""
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]


@pytest.mark.integration
class TestLanceDBIntegration:
    """Integration tests exercising real LanceDB operations."""

    @pytest.mark.asyncio
    async def test_upsert_and_vector_search(self, lance_dir: Path) -> None:
        """Upsert 5 items and verify vector search returns sorted results."""
        backend = LanceDBBackend(persist_dir=str(lance_dir))

        # Use a known pattern: item-0 is the query, others are random
        base_embedding = _random_embedding()
        for i in range(5):
            # Make item-0 closest to query by using the base embedding directly
            emb = base_embedding if i == 0 else _random_embedding()
            await backend.upsert(
                id=f"chunk-{i}",
                content=f"def function_{i}(x): return x * {i}",
                embedding=emb,
                metadata={
                    "file_path": f"src/module_{i}.py",
                    "symbol_name": f"function_{i}",
                    "symbol_kind": "function",
                    "project_id": "proj-integration",
                    "line_start": i * 10 + 1,
                    "line_end": i * 10 + 5,
                },
            )

        results = await backend.query(
            query_embedding=base_embedding,
            top_k=5,
        )

        assert len(results) == 5
        assert all(isinstance(r, VectorResult) for r in results)
        # First result should be the exact match (chunk-0 with base_embedding)
        assert results[0].id == "chunk-0"
        assert results[0].score > results[-1].score

    @pytest.mark.asyncio
    async def test_filter_by_project_id(self, lance_dir: Path) -> None:
        """Verify that project_id filter restricts results."""
        backend = LanceDBBackend(persist_dir=str(lance_dir))

        # Insert items for two different projects
        for project, count in [("proj-A", 3), ("proj-B", 2)]:
            for i in range(count):
                await backend.upsert(
                    id=f"{project}-item-{i}",
                    content=f"code for {project} item {i}",
                    embedding=_random_embedding(),
                    metadata={
                        "file_path": f"{project}/file_{i}.py",
                        "symbol_name": f"func_{i}",
                        "symbol_kind": "function",
                        "project_id": project,
                        "line_start": 1,
                        "line_end": 5,
                    },
                )

        results = await backend.query(
            query_embedding=_random_embedding(),
            top_k=10,
            filter={"project_id": "proj-A"},
        )

        assert len(results) == 3
        assert all(r.metadata["project_id"] == "proj-A" for r in results)

    @pytest.mark.asyncio
    async def test_delete_removes_correct_items(self, lance_dir: Path) -> None:
        """Verify that delete removes only the specified items."""
        backend = LanceDBBackend(persist_dir=str(lance_dir))

        for i in range(3):
            await backend.upsert(
                id=f"del-{i}",
                content=f"content {i}",
                embedding=_random_embedding(),
                metadata={
                    "file_path": f"file_{i}.py",
                    "symbol_name": f"sym_{i}",
                    "symbol_kind": "function",
                    "project_id": "proj-del",
                    "line_start": 1,
                    "line_end": 2,
                },
            )

        # Delete item 1 only
        await backend.delete(ids=["del-1"])

        results = await backend.query(
            query_embedding=_random_embedding(),
            top_k=10,
        )
        result_ids = [r.id for r in results]
        assert "del-1" not in result_ids
        assert "del-0" in result_ids
        assert "del-2" in result_ids

    @pytest.mark.asyncio
    async def test_upsert_replaces_existing(self, lance_dir: Path) -> None:
        """Verify that upserting with same id replaces the content."""
        backend = LanceDBBackend(persist_dir=str(lance_dir))

        emb = _random_embedding()
        await backend.upsert(
            id="replace-me",
            content="original content",
            embedding=emb,
            metadata={
                "file_path": "old.py",
                "symbol_name": "old_func",
                "symbol_kind": "function",
                "project_id": "proj-replace",
                "line_start": 1,
                "line_end": 2,
            },
        )

        # Upsert with same id but different content
        await backend.upsert(
            id="replace-me",
            content="updated content",
            embedding=emb,
            metadata={
                "file_path": "new.py",
                "symbol_name": "new_func",
                "symbol_kind": "function",
                "project_id": "proj-replace",
                "line_start": 10,
                "line_end": 20,
            },
        )

        results = await backend.query(query_embedding=emb, top_k=5)
        matching = [r for r in results if r.id == "replace-me"]
        assert len(matching) == 1
        assert matching[0].content == "updated content"
        assert matching[0].metadata["file_path"] == "new.py"
