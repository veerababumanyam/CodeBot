"""Vector store abstraction with pluggable backends.

Provides a ``VectorStoreBackend`` protocol and two implementations:

- **LanceDBBackend** -- embedded vector database for development and small
  projects.  Uses the synchronous LanceDB API wrapped in
  ``asyncio.to_thread()`` to avoid blocking the event loop (per research
  recommendation on LanceDB async API maturity).
- **QdrantBackend** -- production-grade vector database using the official
  async client.

Both backends store 384-dimensional embeddings (matching
``all-MiniLM-L6-v2``) and support vector search, upsert, delete, and
hybrid search (where available).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class VectorResult(BaseModel):
    """A single search result from the vector store."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class VectorStoreBackend(Protocol):
    """Protocol that all vector store backends must satisfy."""

    async def upsert(
        self,
        id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a vector entry."""
        ...

    async def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Return the ``top_k`` most similar results."""
        ...

    async def delete(self, ids: list[str]) -> None:
        """Remove entries by their IDs."""
        ...

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Combined vector + full-text search with reranking."""
        ...


# ---------------------------------------------------------------------------
# LanceDB backend
# ---------------------------------------------------------------------------


class LanceDBBackend:
    """Embedded LanceDB for development and small projects.

    All synchronous LanceDB operations are wrapped in
    ``asyncio.to_thread()`` so they never block the event loop.
    """

    TABLE_NAME = "code_chunks"

    def __init__(self, persist_dir: str = "data/lancedb") -> None:
        import lancedb as _lancedb  # lazy import

        self._db = _lancedb.connect(persist_dir)
        self._table: Any | None = None

    # -- helpers --------------------------------------------------------

    def _get_or_create_table(self, record: dict[str, Any]) -> tuple[Any, bool]:
        """Return the table and whether it was just created.

        Returns:
            A tuple of ``(table, was_created)``.  If *was_created* is
            ``True`` the table was brand-new and *record* was inserted
            as its first row.
        """
        if self._table is not None:
            return self._table, False
        try:
            self._table = self._db.open_table(self.TABLE_NAME)
            return self._table, False
        except Exception:
            # Table does not exist yet -- create it with the first record.
            self._table = self._db.create_table(self.TABLE_NAME, data=[record])
            return self._table, True

    def _make_record(
        self,
        id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": id,
            "text": content,
            "vector": embedding,
            "file_path": metadata.get("file_path", ""),
            "symbol_name": metadata.get("symbol_name", ""),
            "symbol_kind": metadata.get("symbol_kind", ""),
            "project_id": metadata.get("project_id", ""),
            "line_start": metadata.get("line_start", 0),
            "line_end": metadata.get("line_end", 0),
        }

    # -- public API -----------------------------------------------------

    async def upsert(
        self,
        id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a single record."""
        record = self._make_record(id, content, embedding, metadata)

        def _sync_upsert() -> None:
            table, was_created = self._get_or_create_table(record)
            if was_created:
                # Table was just created with this record as its first row.
                return
            # Delete existing record with same id (if any), then add.
            try:
                table.delete(f"id = '{id}'")
            except Exception:
                pass
            table.add([record])

        await asyncio.to_thread(_sync_upsert)

    async def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Vector similarity search."""

        def _sync_query() -> list[VectorResult]:
            if self._table is None:
                try:
                    self._table = self._db.open_table(self.TABLE_NAME)
                except Exception:
                    return []
            builder = self._table.search(query_embedding).limit(top_k)
            if filter:
                conditions = " AND ".join(
                    f"{k} = '{v}'" for k, v in filter.items()
                )
                builder = builder.where(conditions)
            rows = builder.to_list()
            return [
                VectorResult(
                    id=row.get("id", ""),
                    content=row.get("text", ""),
                    score=1.0 - float(row.get("_distance", 0.0)),
                    metadata={
                        "file_path": row.get("file_path", ""),
                        "symbol_name": row.get("symbol_name", ""),
                        "symbol_kind": row.get("symbol_kind", ""),
                        "project_id": row.get("project_id", ""),
                        "line_start": row.get("line_start", 0),
                        "line_end": row.get("line_end", 0),
                    },
                )
                for row in rows
            ]

        return await asyncio.to_thread(_sync_query)

    async def delete(self, ids: list[str]) -> None:
        """Delete records by ID."""

        def _sync_delete() -> None:
            if self._table is None:
                try:
                    self._table = self._db.open_table(self.TABLE_NAME)
                except Exception:
                    return
            for record_id in ids:
                try:
                    self._table.delete(f"id = '{record_id}'")
                except Exception:
                    logger.warning("Failed to delete id=%s", record_id)

        await asyncio.to_thread(_sync_delete)

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Hybrid (vector + FTS) search with RRF reranking.

        Falls back to vector-only search if the FTS index has not been
        created yet.
        """

        def _sync_hybrid() -> list[VectorResult]:
            if self._table is None:
                try:
                    self._table = self._db.open_table(self.TABLE_NAME)
                except Exception:
                    return []
            try:
                from lancedb.rerankers import RRFReranker

                reranker = RRFReranker()
                builder = (
                    self._table.search(query, query_type="hybrid")
                    .rerank(reranker=reranker)
                    .limit(top_k)
                )
                if filter:
                    conditions = " AND ".join(
                        f"{k} = '{v}'" for k, v in filter.items()
                    )
                    builder = builder.where(conditions)
                rows = builder.to_list()
            except Exception:
                # FTS index not available -- fall back to vector search.
                logger.info(
                    "Hybrid search unavailable, falling back to vector search"
                )
                builder = self._table.search(query_embedding).limit(top_k)
                if filter:
                    conditions = " AND ".join(
                        f"{k} = '{v}'" for k, v in filter.items()
                    )
                    builder = builder.where(conditions)
                rows = builder.to_list()

            return [
                VectorResult(
                    id=row.get("id", ""),
                    content=row.get("text", ""),
                    score=1.0 - float(row.get("_distance", 0.0)),
                    metadata={
                        "file_path": row.get("file_path", ""),
                        "symbol_name": row.get("symbol_name", ""),
                        "symbol_kind": row.get("symbol_kind", ""),
                        "project_id": row.get("project_id", ""),
                        "line_start": row.get("line_start", 0),
                        "line_end": row.get("line_end", 0),
                    },
                )
                for row in rows
            ]

        return await asyncio.to_thread(_sync_hybrid)

    async def create_fts_index(self, field: str = "text") -> None:
        """Create a full-text search index for hybrid queries."""

        def _sync_create_fts() -> None:
            if self._table is None:
                try:
                    self._table = self._db.open_table(self.TABLE_NAME)
                except Exception:
                    return
            self._table.create_fts_index(field, replace=True)

        await asyncio.to_thread(_sync_create_fts)


# ---------------------------------------------------------------------------
# Qdrant backend
# ---------------------------------------------------------------------------


class QdrantBackend:
    """Qdrant server for production deployments.

    Uses the official ``AsyncQdrantClient`` for fully async operations.
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "codebot",
    ) -> None:
        from qdrant_client import AsyncQdrantClient  # lazy import

        self._client = AsyncQdrantClient(url=url)
        self._collection = collection_name
        self._collection_ready = False

    async def _ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        if self._collection_ready:
            return
        from qdrant_client import models

        collections = await self._client.get_collections()
        names = [c.name for c in collections.collections]
        if self._collection not in names:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE,
                ),
            )
        self._collection_ready = True

    async def upsert(
        self,
        id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a single point."""
        from qdrant_client import models

        await self._ensure_collection()
        payload = {**metadata, "text": content}
        await self._client.upsert(
            collection_name=self._collection,
            points=[
                models.PointStruct(
                    id=id,
                    vector=embedding,
                    payload=payload,
                ),
            ],
        )

    async def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Vector similarity search."""
        from qdrant_client import models

        await self._ensure_collection()
        query_filter = None
        if filter:
            must_conditions = [
                models.FieldCondition(
                    key=k,
                    match=models.MatchValue(value=v),
                )
                for k, v in filter.items()
            ]
            query_filter = models.Filter(must=must_conditions)

        response = await self._client.query_points(
            collection_name=self._collection,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k,
        )
        return [
            VectorResult(
                id=str(point.id),
                content=point.payload.get("text", "") if point.payload else "",
                score=point.score if point.score is not None else 0.0,
                metadata={
                    k: v
                    for k, v in (point.payload or {}).items()
                    if k != "text"
                },
            )
            for point in response.points
        ]

    async def delete(self, ids: list[str]) -> None:
        """Remove points by ID."""
        from qdrant_client import models

        await self._ensure_collection()
        await self._client.delete(
            collection_name=self._collection,
            points_selector=models.PointIdsList(points=ids),
        )

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorResult]:
        """Hybrid search -- falls back to vector search for Qdrant.

        Qdrant's BM25 hybrid search requires additional index setup that
        is deferred to a later phase.  For now this delegates to
        ``query()``.
        """
        return await self.query(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filter,
        )
