---
phase: 05-context-management
plan: 02
subsystem: context
tags: [lancedb, qdrant, tree-sitter, vector-store, code-indexing, embeddings, hybrid-search]

# Dependency graph
requires:
  - phase: 01-foundation-and-scaffolding
    provides: "Monorepo structure, pyproject.toml, Python project scaffolding"
provides:
  - "VectorStoreBackend protocol for pluggable vector stores"
  - "LanceDBBackend for embedded development vector search"
  - "QdrantBackend for production vector search"
  - "CodeIndexer with Tree-sitter parsing for Python/TypeScript/JavaScript"
  - "VectorResult model for search results"
  - "CodeSymbol model for extracted code symbols"
affects: [context-adapter, context-tiers, agent-sdk, implementation-agents]

# Tech tracking
tech-stack:
  added: [lancedb 0.30.0, qdrant-client 1.17.0, sentence-transformers 5.3.0, tree-sitter 0.25.2, tree-sitter-python 0.25.0, tree-sitter-typescript 0.23.2, tree-sitter-javascript 0.25.0]
  patterns: [Protocol-based backend abstraction, sync-to-async wrapping via asyncio.to_thread, Tree-sitter QueryCursor API for symbol extraction]

key-files:
  created:
    - apps/server/src/codebot/context/vector_store.py
    - apps/server/src/codebot/context/code_indexer.py
    - apps/server/src/codebot/context/models.py
    - tests/unit/context/test_vector_store.py
    - tests/unit/context/test_code_indexer.py
    - tests/integration/context/test_vector_search.py
    - tests/integration/context/conftest.py
  modified:
    - apps/server/pyproject.toml

key-decisions:
  - "Used Query() constructor + QueryCursor instead of deprecated language.query().captures() API for tree-sitter 0.25.x"
  - "TypeScript grammar uses type_identifier (not identifier) for class names -- adapted queries accordingly"
  - "LanceDB sync API wrapped in asyncio.to_thread() per research recommendation (async API not fully mature)"
  - "Qdrant hybrid_search falls back to vector-only search (BM25 index setup deferred)"

patterns-established:
  - "Protocol-based backend abstraction: VectorStoreBackend defines async interface, implementations handle backend-specific details"
  - "Sync-to-async wrapping: all LanceDB sync operations wrapped in asyncio.to_thread() to avoid blocking event loop"
  - "Tree-sitter QueryCursor pattern: Query(language, pattern) + QueryCursor(query).matches(node) for symbol extraction"
  - "Per-language grammar registration: _LANGUAGES dict maps file extensions to Language objects"

requirements-completed: [CTXT-04, CTXT-05]

# Metrics
duration: 8min
completed: 2026-03-18
---

# Phase 5 Plan 2: Vector Store & Code Indexer Summary

**LanceDB/Qdrant vector store backends with Tree-sitter code indexer extracting Python/TypeScript/JavaScript symbols via structural AST queries**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-18T10:05:27Z
- **Completed:** 2026-03-18T10:14:12Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 10

## Accomplishments
- VectorStoreBackend protocol with pluggable LanceDB (dev) and Qdrant (prod) implementations
- CodeIndexer extracting functions, classes, methods, and imports from Python, TypeScript, JavaScript, and TSX files
- All 23 tests passing (13 unit for code indexer, 6 unit for vector store, 4 integration for LanceDB)
- Hybrid search with RRF reranking support (falls back to vector-only when FTS index unavailable)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for vector store and code indexer** - `d7edaf5` (test)
2. **Task 1 (GREEN): Implement vector store backends and code indexer** - `e3af6d0` (feat)

_TDD task with RED-GREEN commits. No REFACTOR needed._

## Files Created/Modified
- `apps/server/src/codebot/context/vector_store.py` - VectorStoreBackend protocol + LanceDBBackend + QdrantBackend implementations
- `apps/server/src/codebot/context/code_indexer.py` - CodeIndexer with Tree-sitter parsing for Python/TS/JS/TSX
- `apps/server/src/codebot/context/models.py` - CodeSymbol and Priority Pydantic models
- `apps/server/pyproject.toml` - Added lancedb, qdrant-client, sentence-transformers, tree-sitter dependencies
- `tests/unit/context/test_vector_store.py` - 6 unit tests for VectorResult model and LanceDBBackend CRUD
- `tests/unit/context/test_code_indexer.py` - 13 unit tests for symbol extraction across languages
- `tests/integration/context/test_vector_search.py` - 4 integration tests for LanceDB search, filter, delete
- `tests/integration/context/conftest.py` - Shared fixtures for integration tests

## Decisions Made
- **tree-sitter 0.25.x API change:** Used `Query()` constructor + `QueryCursor.matches()` instead of deprecated `language.query().captures()` API. The research examples used the old API; the installed version requires the new pattern.
- **TypeScript type_identifier:** TypeScript grammar uses `type_identifier` node type for class names instead of `identifier`. Adapted query patterns and name extraction logic.
- **Qdrant hybrid search deferred:** QdrantBackend.hybrid_search() falls back to vector-only search since BM25 index setup requires additional infrastructure configuration.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] tree-sitter 0.25.x API breaking change**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Research examples used `language.query(pattern).captures(node)` which is deprecated/removed in tree-sitter 0.25.2. The Query object has no `captures` method.
- **Fix:** Switched to `Query(language, pattern)` constructor + `QueryCursor(query).matches(node)` which returns `(pattern_idx, dict[str, list[Node]])` tuples.
- **Files modified:** `apps/server/src/codebot/context/code_indexer.py`
- **Verification:** All 13 code indexer tests pass
- **Committed in:** e3af6d0

**2. [Rule 1 - Bug] TypeScript class query pattern used wrong node type**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** TypeScript grammar uses `type_identifier` for class declaration names, not `identifier`. Query `(class_declaration name: (identifier) @name)` raised "Impossible pattern" error.
- **Fix:** Changed `.ts` and `.tsx` class queries to use `(type_identifier)`. Updated `_get_name()` helper to also recognize `type_identifier` nodes.
- **Files modified:** `apps/server/src/codebot/context/code_indexer.py`
- **Verification:** TypeScript extraction tests pass
- **Committed in:** e3af6d0

**3. [Rule 1 - Bug] LanceDB upsert not replacing existing records**
- **Found during:** Task 1 (GREEN phase, integration tests)
- **Issue:** `_get_or_create_table()` created table with the first record, but subsequent upserts with the same ID failed to replace because of overly aggressive early-return logic checking `count_rows() == 1`.
- **Fix:** Refactored `_get_or_create_table()` to return `(table, was_created)` tuple. Only skip the delete-then-add cycle when the table was literally just created with this exact record.
- **Files modified:** `apps/server/src/codebot/context/vector_store.py`
- **Verification:** `test_upsert_replaces_existing` integration test passes
- **Committed in:** e3af6d0

**4. [Rule 3 - Blocking] Created models.py since Plan 01 not yet complete**
- **Found during:** Task 1 (setup)
- **Issue:** Plan 01 (same wave) had not yet created `models.py` with `CodeSymbol` class that this plan depends on.
- **Fix:** Created `models.py` with `Priority` enum and `CodeSymbol` model matching the interface spec.
- **Files modified:** `apps/server/src/codebot/context/models.py`
- **Verification:** All imports resolve correctly
- **Committed in:** e3af6d0

---

**Total deviations:** 4 auto-fixed (3 bugs, 1 blocking dependency)
**Impact on plan:** All auto-fixes necessary for correctness. tree-sitter API change and TypeScript grammar differences were not documented in research. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required. LanceDB runs embedded (in-process), Qdrant is only needed for production deployment.

## Next Phase Readiness
- Vector store and code indexer are ready for use by the ContextAdapter (Plan 03)
- L2 retrieval (CTXT-03) can now be built on top of VectorStoreBackend.query()
- CodeIndexer can be used during codebase indexing to populate the vector store
- Qdrant backend ready but requires running Qdrant server for production use

## Self-Check: PASSED

All 8 created files verified present. Both commits (d7edaf5, e3af6d0) verified in git log.

---
*Phase: 05-context-management*
*Completed: 2026-03-18*
