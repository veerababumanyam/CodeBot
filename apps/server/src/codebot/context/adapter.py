"""Context assembly adapter -- main entry point for agent context.

The ``ContextAdapter`` is the single interface that every agent
invocation uses to get its context.  It wires together:

- **ThreeTierLoader** (Plan 01) for L0/L1 loading
- **VectorStoreBackend + CodeIndexer** (Plan 02) for L2 retrieval
- **ContextCompressor** (Plan 03) for budget enforcement

Priority mapping:

- **L0** (project essentials) -> ``CRITICAL`` -- never dropped
- **Task data** -> ``HIGH`` -- almost never dropped
- **L1** (phase-scoped) -> ``MEDIUM`` -- summarized if budget tight
- **L2** (vector store) -> ``LOW`` -- evicted first

This module is intentionally dependency-injected so that all
collaborators can be mocked in tests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from codebot.context.models import AgentContext, L0Context, Priority

if TYPE_CHECKING:
    from agent_sdk.models.task import TaskSchema
    from codebot.context.code_indexer import CodeIndexer
    from codebot.context.compressor import ContextCompressor
    from codebot.context.tiers import ThreeTierLoader
    from codebot.context.vector_store import VectorStoreBackend

logger = logging.getLogger(__name__)


class ContextAdapter:
    """Orchestrates L0/L1/L2 context assembly with budget enforcement.

    The adapter is the main entry point for building an ``AgentContext``
    that can be passed to any agent.  Dependencies are injected through
    the constructor so that tests can provide mocks.

    Args:
        agent_role: The role of the agent (e.g., ``BACKEND_DEV``).
        token_budget: Maximum token budget for the assembled context.
        loader: A ``ThreeTierLoader`` for L0/L1 loading.
        compressor: A ``ContextCompressor`` for budget enforcement.
        vector_store: Optional ``VectorStoreBackend`` for L2 retrieval.
        code_indexer: Optional ``CodeIndexer`` for code search.
        model: LLM model name (for tokenizer selection).
    """

    __slots__ = (
        "_agent_role",
        "_code_indexer",
        "_compressor",
        "_loader",
        "_model",
        "_token_budget",
        "_vector_store",
    )

    def __init__(
        self,
        *,
        agent_role: str,
        token_budget: int,
        loader: ThreeTierLoader,
        compressor: ContextCompressor,
        vector_store: VectorStoreBackend | None = None,
        code_indexer: CodeIndexer | None = None,
        model: str = "gpt-4o",
    ) -> None:
        self._agent_role = agent_role
        self._token_budget = token_budget
        self._loader = loader
        self._compressor = compressor
        self._vector_store = vector_store
        self._code_indexer = code_indexer
        self._model = model

    async def build_context(
        self,
        task: TaskSchema,
        agent_system_prompt: str = "",
        pipeline_phase: str = "",
    ) -> AgentContext:
        """Assemble a full ``AgentContext`` for the given task.

        Steps:

        1. Load L0 context (``CRITICAL`` priority).
        2. Add task data (``HIGH`` priority).
        3. Load L1 context (``MEDIUM`` priority).
        4. Retrieve L2 context from vector store (``LOW`` priority).
        5. Compress if over budget.

        Args:
            task: The task to build context for.
            agent_system_prompt: System prompt for the agent.
            pipeline_phase: Current pipeline phase name.

        Returns:
            A populated ``AgentContext`` within its token budget.
        """
        context = AgentContext(budget=self._token_budget, model=self._model)

        # Step 1: L0 -- CRITICAL priority, always loaded
        l0 = await self._loader.load_l0(
            agent_system_prompt=agent_system_prompt,
            pipeline_phase=pipeline_phase,
        )
        l0_text = self._format_l0(l0)
        context.add(l0_text, priority=Priority.CRITICAL, source="l0")

        # Step 2: Task data -- HIGH priority
        task_text = self._format_task(task)
        context.add(task_text, priority=Priority.HIGH, source="task")

        # Step 3: L1 -- MEDIUM priority, loaded per phase/role
        l1 = await self._loader.load_l1(
            phase=pipeline_phase,
            agent_role=self._agent_role,
        )
        if l1.phase_requirements:
            context.add(
                l1.phase_requirements,
                priority=Priority.MEDIUM,
                source="l1_requirements",
            )
        if l1.architecture_decisions:
            context.add(
                l1.architecture_decisions,
                priority=Priority.MEDIUM,
                source="l1_architecture",
            )

        # Step 4: L2 -- LOW priority, vector store retrieval (optional)
        if self._vector_store is not None and context.has_budget(reserve=500):
            try:
                # Placeholder embedding -- in production this would use
                # sentence-transformers or another embedding model.
                query_embedding = [0.0] * 384
                results = await self._vector_store.query(
                    query_embedding=query_embedding,
                    top_k=5,
                    filter={"project_id": str(task.project_id)},
                )
                for result in results:
                    if context.has_budget():
                        context.add(
                            result.content,
                            priority=Priority.LOW,
                            source="l2_vector",
                        )
            except Exception:
                logger.debug(
                    "L2 vector store retrieval failed (best-effort), "
                    "continuing without L2 context.",
                    exc_info=True,
                )

        # Step 5: Compress if over budget
        if context.is_over_budget():
            await self._compressor.compress(context)

        return context

    # ------------------------------------------------------------------
    # Private formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_l0(l0: L0Context) -> str:
        """Format L0 context into a readable string.

        Args:
            l0: The L0 context data.

        Returns:
            Formatted markdown-style string.
        """
        tech = "\n".join(f"- {t}" for t in l0.tech_stack)
        constraints = "\n".join(f"- {c}" for c in l0.constraints)
        return (
            f"# Project: {l0.project_name}\n"
            f"{l0.project_description}\n\n"
            f"## Tech Stack\n{tech}\n\n"
            f"## Conventions\n{l0.conventions}\n\n"
            f"## Agent Instructions\n{l0.agent_system_prompt}\n\n"
            f"## Constraints\n{constraints}"
        )

    @staticmethod
    def _format_task(task: TaskSchema) -> str:
        """Format task data into a readable string.

        Args:
            task: The task schema.

        Returns:
            Formatted markdown-style string.
        """
        return (
            f"# Current Task: {task.title}\n"
            f"{task.description}\n\n"
            f"Agent Type: {task.assigned_agent_type}\n"
            f"Priority: {task.priority}"
        )
