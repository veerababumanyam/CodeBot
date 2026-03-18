---
name: codebot-context-memory
description: >
  Working with CodeBot's 3-tier context management and memory system.
  Covers the Context Adapter, vector store, code indexer, compression,
  episodic memory, MCP integration, and token budget enforcement.
tags:
  - codebot
  - context
  - memory
  - vector-store
  - agents
globs:
  - "apps/server/src/codebot/context/**/*.py"
  - "apps/server/src/codebot/context/*.py"
  - ".codebot/context/**/*"
version: "1.0"
---

# CodeBot Context Management and Memory System

## Overview

The Context Management System is a built-in CodeBot feature that ensures each
agent receives precisely the information it needs -- no more, no less. It
implements the MASFactory Context Adapter pattern with a three-tier hierarchical
loading system, persistent episodic memory, and vector-based semantic search.

Source code: `apps/server/src/codebot/context/`

Key modules:
- `adapter.py` -- ContextAdapter (unified interface, MASFactory pattern)
- `tiers.py` -- ThreeTierLoader (L0/L1/L2 tier management)
- `memory.py` -- MemoryManager (persistent episodic memory)
- `vector_store.py` -- VectorStore (embedding storage and retrieval)
- `code_indexer.py` -- CodeIndexer (Tree-sitter code indexing)
- `compressor.py` -- ContextCompressor (summarization and compression)
- `mcp.py` -- MCP protocol integration for context tool/resource exposure

Additional infrastructure:
- **DuckDB** -- In-process OLAP for context analytics queries
- **LlamaIndex** -- RAG framework for advanced retrieval pipelines

Tech: Python 3.12+, strict mypy, ruff, async-first design.

---

## 1. Three-Tier Context Architecture

### Tier L0 -- Always Loaded (~2K tokens)

L0 context is mandatory and loaded for every agent invocation. It provides the
minimal project awareness every agent needs.

Contents:
- Project name, description, tech stack
- Directory structure (top 2 levels)
- Key config files (package.json, pyproject.toml)
- Coding conventions summary
- Current pipeline phase and status
- Agent role instructions and system prompt
- Critical constraints and non-functional requirements

Storage: `.codebot/context/L0/` (summary.md, conventions.md)

### Tier L1 -- On-Demand (~10-20K tokens)

L1 context is loaded per-task based on the agent's role and current task type.
The Context Adapter uses rule-based matching to determine what to load.

Contents:
- Relevant source files for the current task
- Architecture documents and design decisions
- API specifications (OpenAPI/GraphQL schemas)
- Database schemas and migration history
- Test results from upstream agents
- Security scan reports relevant to current task
- Upstream agent outputs (code review comments, etc.)

Storage: `.codebot/context/L1/` (architecture/, schemas/, api-specs/)

Role-based loading rules:
- Frontend Dev -> UI components, design specs, API specs
- Backend Dev -> database schemas, API specs, business logic
- Tester -> source under test, existing tests, coverage report
- Debugger -> failing tests, stack traces, recent changes

### Tier L2 -- Deep Retrieval (~20K tokens)

L2 context is deferred and pulled on-demand by the agent during execution via
registered MCP tools or RAG retrieval endpoints.

Contents:
- Full codebase semantic search (vector + keyword hybrid)
- External documentation and API references
- Research results and reference implementations
- Historical project decisions (ADRs)
- Dependency documentation and usage examples

Storage: `.codebot/context/L2/` (research/, references/) + vector store

### Agent Context Tier Settings

Each agent has a `context_tier` configuration that determines its maximum
context access level:

| Setting    | Loaded Tiers     | Typical Agents                     |
|------------|------------------|------------------------------------|
| `L0`       | L0 only          | Simple utility agents              |
| `L0+L1`    | L0 + L1          | Review agents, planners            |
| `L0+L1+L2` | L0 + L1 + L2    | Coding agents, debuggers, testers  |

---

## 2. Context Adapter Implementation

The `ContextAdapter` is the central interface that assembles context payloads
for each agent invocation. One instance per agent execution.

### Construction

```python
adapter = ContextAdapter(
    agent_role=AgentRole.BACKEND_DEV,
    token_budget=32_000,
    loader=ThreeTierLoader(project_root),
    memory=MemoryManager(db_path),
    vector_store=VectorStore(collection),
    code_indexer=CodeIndexer(project_root),
    compressor=ContextCompressor(model_client),
)
```

### Context Assembly Pipeline

The `build_context(task)` method assembles context in priority order:

1. **L0 load** (priority: CRITICAL) -- always-loaded project summary
2. **Task data** (priority: HIGH) -- extracted from SharedState
3. **L1 load** (priority: MEDIUM) -- relevant files via CodeIndexer
4. **L2 retrieval** (priority: LOW) -- RAG results from vector store
5. **Memory recall** -- persistent memories from prior executions
6. **Compression** -- if over budget, compress via ContextCompressor

Each step checks `context.has_budget()` before adding more content. Items are
added with a priority level so lower-priority content is evicted first when
the token budget is exceeded.

### SharedState Integration

The graph engine's `SharedState` propagates context between agents. The adapter
reads upstream outputs from SharedState:

```python
task_data = self._extract_task_context(task)
# Pulls: task.description, task.dependencies_output, task.shared_state
```

---

## 3. Vector Store Integration

### Backend Selection

| Environment | Backend | Notes                                |
|-------------|---------|--------------------------------------|
| Development | LanceDB | Embedded, zero-config, file-based    |
| Production  | Qdrant  | Distributed, scalable, gRPC API      |

### Indexing Pipeline

1. Files are chunked by the CodeIndexer (Tree-sitter for code, paragraph
   splitting for docs)
2. Chunks are embedded via the configured embedding model
3. Embeddings are stored in the vector store with metadata (file path,
   language, symbol names, project_id)

### Querying

```python
results = await vector_store.query(
    query=task.description,
    top_k=5,
    filter={"project_id": task.project_id},
)
```

Retrieval uses hybrid search: vector similarity + BM25 keyword matching.
Results are re-ranked by relevance score before inclusion in context.

### Relevance Scoring

Results are scored on:
- Cosine similarity to query embedding
- BM25 keyword overlap
- Recency (recently modified files score higher)
- Symbol-level relevance (function/class names matching task terms)

---

## 4. Code Indexer (Tree-sitter Integration)

The `CodeIndexer` uses Tree-sitter for language-aware code parsing and symbol
extraction.

### Capabilities

- Parse source files into ASTs for supported languages
- Extract symbols: functions, classes, methods, interfaces, types, constants
- Build a project-wide symbol index for fast lookup
- Find files relevant to a task description by matching against symbol names
  and docstrings
- Generate code summaries (function signatures, class outlines) for L1 context

### Symbol Extraction

```python
indexer = CodeIndexer(project_root="/path/to/project")
await indexer.index()  # Full project indexing

# Find relevant files for a task
relevant = await indexer.find_relevant("implement user authentication endpoint")
# Returns: List[FileContext] with path, symbols, relevance_score
```

### Supported Languages

Tree-sitter grammars are loaded for: Python, TypeScript, JavaScript, Go, Rust,
Java, Kotlin, Swift, C#, Ruby, and more. The indexer auto-detects language from
file extensions.

---

## 5. Context Compression Strategies

The `ContextCompressor` reduces context size when the assembled payload exceeds
the agent's token budget.

### Compression Methods

1. **Summary compression** -- Use the LLM to summarize verbose content into
   concise summaries (architecture docs, long code files)
2. **Symbol-only compression** -- Replace full file contents with function
   signatures and class outlines (via CodeIndexer)
3. **Priority eviction** -- Drop lowest-priority items first (L2 before L1,
   LOW before MEDIUM)
4. **Conversation history compression** -- Summarize older conversation turns
   while preserving recent exchanges verbatim

### Compression Pipeline

```python
if context.is_over_budget():
    context = await compressor.compress(context)
```

The compressor iterates:
1. Evict LOW priority items until within budget
2. If still over, summarize MEDIUM priority items
3. If still over, summarize HIGH priority items (preserving key data)
4. L0 (CRITICAL) is never compressed or evicted

---

## 6. Memory Persistence (Episodic Memory)

The `MemoryManager` provides cross-session context persistence so agents can
learn from prior executions.

### Lifecycle Hooks

- `on_task_start` -- Load relevant memories for the starting task
- `on_task_complete` -- Save learnings, decisions, and outcomes
- `on_pipeline_end` -- Consolidate and compress session memories

### Memory Types

- **Decision history** -- Architecture and implementation decisions with rationale
- **Agent learnings** -- Patterns discovered, mistakes made, workarounds found
- **Error patterns** -- Recurring errors and their resolutions
- **Conversation summaries** -- Compressed prior interactions

### Storage

- Development: LanceDB (vectors) + SQLite (structured metadata)
- Production: Qdrant (vectors) + SQLite (structured metadata)

### Recall

```python
memories = await memory.recall(
    agent_role=AgentRole.BACKEND_DEV,
    task_type=TaskType.IMPLEMENT,
    limit=10,
)
```

Memories are retrieved by semantic similarity to the current task, filtered by
agent role and task type. Stale memories are periodically compressed via
semantic summarization.

### Progressive Disclosure

Memories are returned in layers:
1. **Summary** -- one-line summary of the memory
2. **Full** -- complete memory content (loaded if agent requests it)
3. **Linked** -- related memories and source references

---

## 7. Token Budget Management

Each agent has a configured token budget that the ContextAdapter enforces.

### Budget Allocation

```
Total Agent Budget (e.g., 128K tokens)
  - System prompt overhead:   ~1K tokens
  - L0 context:               ~2K tokens
  - Task data:                ~2K tokens
  - L1 context:               ~10-20K tokens
  - L2 retrieval:             ~20K tokens
  - Memory:                   ~5K tokens
  - Reserved for generation:  remaining tokens
```

### Enforcement

The `AgentContext` object tracks token usage as items are added:

```python
context = AgentContext(budget=self.token_budget)
context.add(l0, priority=Priority.CRITICAL)  # Always added
# ...
if context.has_budget():
    context.add(l1_item, priority=Priority.MEDIUM)
# After assembly:
if context.is_over_budget():
    context = await self.compressor.compress(context)
```

Token counting uses tiktoken (for OpenAI models) or model-specific tokenizers.
The budget reserves space for the agent's output generation.

---

## 8. MCP Context Sources

The `mcp.py` module exposes context capabilities as MCP (Model Context Protocol)
tools and resources that agents can invoke during execution.

### Registered MCP Tools

- **semantic_search** -- Query the vector store for relevant code/docs
- **read_file** -- Load a specific file into context (L1/L2)
- **list_symbols** -- List functions/classes in a file via CodeIndexer
- **recall_memory** -- Retrieve episodic memories
- **search_codebase** -- Keyword search across the project

### MCP Resources

- **project_summary** -- L0 project summary (always available)
- **architecture_docs** -- L1 architecture documents
- **api_specs** -- L1 API specifications

L2 context hooks are registered as deferred MCP tools so agents can pull deep
context on-demand without preloading it.

---

## 9. Testing Context Management

### Unit Tests

Test each module independently with mocked dependencies:

```python
# Test ContextAdapter assembly
async def test_build_context_respects_budget():
    adapter = ContextAdapter(
        agent_role=AgentRole.BACKEND_DEV,
        token_budget=4000,
        loader=mock_loader,
        memory=mock_memory,
        vector_store=mock_vector_store,
        code_indexer=mock_indexer,
        compressor=mock_compressor,
    )
    context = await adapter.build_context(mock_task)
    assert context.token_count <= 4000

# Test ThreeTierLoader
async def test_l0_always_loaded():
    loader = ThreeTierLoader(project_root=tmp_path)
    l0 = await loader.load_l0()
    assert l0 is not None
    assert l0.token_count < 2500

# Test CodeIndexer symbol extraction
async def test_symbol_extraction():
    indexer = CodeIndexer(project_root=tmp_path)
    await indexer.index()
    symbols = indexer.get_symbols("src/auth.py")
    assert any(s.name == "authenticate" for s in symbols)

# Test ContextCompressor
async def test_compression_within_budget():
    context = AgentContext(budget=4000)
    context.add(large_content, priority=Priority.LOW)  # 10K tokens
    compressed = await compressor.compress(context)
    assert compressed.token_count <= 4000
```

### Integration Tests

- Test full context assembly pipeline with a real project directory
- Test vector store indexing and retrieval round-trip
- Test memory persistence across simulated sessions
- Test MCP tool invocations return valid context

### Test Fixtures

Place test project structures in `tests/fixtures/context/`:
- `sample_project/` -- minimal project with `.codebot/context/L0/`, `L1/`, `L2/`
- `sample_codebase/` -- Python/TypeScript files for CodeIndexer testing

### Key Assertions

- L0 is always present in assembled context regardless of budget
- Token budget is never exceeded after compression
- Vector store queries return results sorted by relevance
- Memory recall filters by agent role and task type
- Compression preserves CRITICAL priority items unchanged

---

## Common Patterns

### Adding a New Context Source

1. Define the source in the appropriate tier (L0/L1/L2)
2. Update `ThreeTierLoader` to load the new source
3. If L2, register an MCP tool in `mcp.py` for on-demand access
4. Update the `ContextAdapter` role-based rules if the source is role-specific
5. Add token budget estimates for the new source

### Adjusting Agent Token Budgets

Agent budgets are configured in the agent catalog. To change:

1. Update the agent's `token_budget` in its configuration
2. Verify context assembly still works within the new budget
3. Run budget tests to ensure no overflow

### Debugging Context Issues

When an agent produces poor output, check context quality:

1. Enable context logging: set `CODEBOT_CONTEXT_DEBUG=1`
2. Inspect the assembled `AgentContext` -- check which tiers loaded
3. Verify vector store has indexed the relevant files
4. Check if compression removed critical information
5. Review memory recall results for relevance

## Documentation Lookup (Context7)

Before implementing context/memory features, use Context7 to fetch current docs:

```
mcp__plugin_context7_context7__resolve-library-id("LlamaIndex")
mcp__plugin_context7_context7__query-docs(id, "RAG pipeline ingestion retriever query engine")

mcp__plugin_context7_context7__resolve-library-id("LanceDB")
mcp__plugin_context7_context7__query-docs(id, "Python API table search vector index hybrid")

mcp__plugin_context7_context7__resolve-library-id("Qdrant")
mcp__plugin_context7_context7__query-docs(id, "collection points search filter payload")

mcp__plugin_context7_context7__resolve-library-id("DuckDB")
mcp__plugin_context7_context7__query-docs(id, "Python API analytics aggregate window functions")
```

LlamaIndex and LanceDB APIs change frequently. Always verify current class names and import paths.
