"""CheckpointManager: manages graph execution checkpoints via LangGraph's checkpoint system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


class CheckpointManager:
    """Manages graph execution checkpoints via LangGraph's checkpoint system."""

    def __init__(self, checkpointer: AsyncPostgresSaver | MemorySaver) -> None:
        self._checkpointer = checkpointer

    @classmethod
    async def from_postgres(cls, db_uri: str) -> CheckpointManager:
        """Create a CheckpointManager with PostgreSQL persistence.

        Args:
            db_uri: PostgreSQL connection string, e.g.
                'postgresql://user:pass@localhost:5432/codebot'
        """
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        checkpointer = AsyncPostgresSaver.from_conn_string(db_uri)
        await checkpointer.setup()
        return cls(checkpointer=checkpointer)

    @classmethod
    def from_memory(cls) -> CheckpointManager:
        """Create a CheckpointManager with in-memory storage (for testing)."""
        return cls(checkpointer=MemorySaver())

    @property
    def checkpointer(self) -> AsyncPostgresSaver | MemorySaver:
        """Return the underlying checkpointer instance."""
        return self._checkpointer

    async def setup(self) -> None:
        """Initialize checkpoint tables (idempotent). Only needed for Postgres."""
        if isinstance(self._checkpointer, MemorySaver):
            return
        # For Postgres checkpointers, call setup()
        await self._checkpointer.setup()

    async def get_latest_checkpoint_id(self, thread_id: str) -> str | None:
        """Get the latest checkpoint ID for a thread, or None if no checkpoints exist."""
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await self._checkpointer.aget_tuple(config)
        if checkpoint_tuple is None:
            return None
        return checkpoint_tuple.config["configurable"].get("checkpoint_id")


async def create_checkpointer(db_uri: str) -> Any:
    """Create and initialize a PostgreSQL checkpointer."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    checkpointer = AsyncPostgresSaver.from_conn_string(db_uri)
    await checkpointer.setup()
    return checkpointer


async def resume_from_checkpoint(
    compiled_graph: Any,
    thread_id: str,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    """Resume graph execution from a checkpoint.

    If checkpoint_id is None, resumes from the latest checkpoint.
    Pass None as input to continue from saved state.
    """
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id
    return await compiled_graph.ainvoke(None, config)
