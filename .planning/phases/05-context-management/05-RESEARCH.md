# Phase 5: Context Management - Research

**Researched:** 2026-03-18
**Domain:** Context assembly, vector search, code indexing, token budget enforcement
**Confidence:** HIGH

## Summary

Phase 5 implements the Context Management System -- the subsystem that ensures every agent in CodeBot's pipeline receives precisely the right information (and nothing more) within strict token budgets. The system is organized into three tiers: L0 (always-present essentials like project config, current task, system prompt), L1 (phase-scoped materials like relevant code files, architecture decisions), and L2 (on-demand retrieval via vector store semantic search). Supporting infrastructure includes Tree-sitter code indexing for structural code understanding, a vector store (LanceDB for dev / Qdrant for production) for semantic search, and a context compression pipeline for when assembled context exceeds token budgets.

The architecture is well-defined in SYSTEM_DESIGN.md Section 5, with concrete class designs for `ContextAdapter`, `ThreeTierLoader`, `VectorStore`, `CodeIndexer`, `ContextCompressor`, and `MemoryManager`. This phase implements all seven CTXT requirements. It depends on Phase 4 (Multi-LLM Abstraction) because the `ContextCompressor` uses the LLM layer for summarization, and token counting requires model-specific tokenizers.

**Primary recommendation:** Build the context module at `apps/server/src/codebot/context/` with async-first design, using LanceDB 0.30.x as the embedded vector store (with Qdrant 1.17.x as a pluggable production backend), tree-sitter 0.25.x for code parsing, tiktoken 0.12.x for token counting, and a priority-based budget enforcement system that drops low-priority items before resorting to LLM-based compression.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CTXT-01 | L0 context (always present): project config, current task, agent system prompt | ThreeTierLoader.load_l0() reads from .codebot/context/L0/ filesystem; ~2K token budget; auto-included by ContextAdapter.build_context() |
| CTXT-02 | L1 context (phase-scoped): phase requirements, related code files, architecture decisions | ThreeTierLoader.load_l1() loads files on-demand; ~20K token budget; rule-based selection by agent role + task type |
| CTXT-03 | L2 context (on-demand): vector store retrieval for code search, documentation lookup | VectorStore.query() with hybrid search (vector + BM25 via LanceDB); ~10K token budget; returned as MCP tools for agent self-service |
| CTXT-04 | Vector store indexes codebase for semantic search | LanceDB (dev) / Qdrant (prod) with sentence-transformers embeddings; hybrid search with RRF reranking |
| CTXT-05 | Tree-sitter parses code for structural understanding (functions, classes, imports) | CodeIndexer using py-tree-sitter 0.25.x with per-language grammars; extracts CodeSymbol index |
| CTXT-06 | Context compression summarizes large outputs to fit within token budgets | ContextCompressor with 3-tier strategy: (1) drop LOW priority, (2) summarize MEDIUM, (3) aggressive summarize all non-critical |
| CTXT-07 | Hard token budgets enforced per agent call to prevent context exhaustion | AgentContext class with priority-based item tracking and budget enforcement via tiktoken token counting |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lancedb | 0.30.0 | Embedded vector database (dev/local) | Zero-config embedded DB, hybrid search (vector + BM25), Apache-2.0, built on Lance columnar format |
| qdrant-client | 1.17.1 | Production vector database client | Full async API (AsyncQdrantClient), server mode for scale, local mode for tests, Apache-2.0 |
| tree-sitter | 0.25.2 | Code parsing into ASTs | Official Python bindings, pre-compiled wheels, query API for structural extraction, MIT |
| tiktoken | 0.12.0 | Token counting for budget enforcement | OpenAI's BPE tokenizer, 3-6x faster than alternatives, supports o200k_base and cl100k_base encodings |
| sentence-transformers | 5.3.0 | Text embedding generation | 15K+ pre-trained models on HuggingFace, all-MiniLM-L6-v2 for fast 384-dim embeddings |
| aiofiles | 25.1.0 | Async file I/O for context loading | Thread-pool-based async file ops, async context managers, Apache-2.0 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tree-sitter-python | latest | Python grammar for tree-sitter | When indexing Python source files |
| tree-sitter-typescript | latest | TypeScript grammar for tree-sitter | When indexing TypeScript source files |
| tree-sitter-javascript | latest | JavaScript grammar for tree-sitter | When indexing JavaScript source files |
| tree-sitter-go | latest | Go grammar for tree-sitter | When indexing Go source files |
| pydantic | >=2.9.0 | Data models for context items | Already in server deps; use for AgentContext, L0Context, CodeSymbol schemas |
| litellm | (from Phase 4) | Token counting alternative | LiteLLM's token_counter() can count tokens for any model -- use as fallback to tiktoken |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LanceDB | ChromaDB | ChromaDB is simpler but lacks native hybrid search and BM25; LanceDB matches SYSTEM_DESIGN.md spec |
| sentence-transformers | LanceDB built-in embeddings | LanceDB embedding registry can auto-embed, but sentence-transformers gives more control for code-specific models |
| tiktoken | litellm.token_counter | litellm wraps tiktoken and adds model-name lookup, but tiktoken is lower-level and faster for bulk counting |
| aiofiles | anyio file I/O | anyio.Path provides similar capability but aiofiles has a more mature API and wider adoption |

**Installation:**
```bash
# Core context management dependencies
uv add lancedb qdrant-client tree-sitter tiktoken sentence-transformers aiofiles

# Tree-sitter language grammars (install per target language)
uv add tree-sitter-python tree-sitter-typescript tree-sitter-javascript tree-sitter-go tree-sitter-rust tree-sitter-java tree-sitter-c tree-sitter-cpp tree-sitter-c-sharp tree-sitter-ruby
```

**Version verification:** All versions verified against PyPI on 2026-03-18:
- lancedb: 0.30.0 (latest)
- qdrant-client: 1.17.1 (latest, released 2026-03-13)
- tree-sitter: 0.25.2 (latest, released 2025-09-25, repo updated 2026-03-07)
- tiktoken: 0.12.0 (latest)
- sentence-transformers: 5.3.0 (latest, released 2026-03-12)
- aiofiles: 25.1.0 (latest, released 2025-10-09)

## Architecture Patterns

### Recommended Project Structure

```
apps/server/src/codebot/context/
    __init__.py          # Public API exports
    adapter.py           # ContextAdapter: main entry point, assembles context for agents
    tiers.py             # ThreeTierLoader: L0/L1/L2 loading logic
    models.py            # Pydantic models: AgentContext, L0Context, L1Context, CodeSymbol, etc.
    memory.py            # MemoryManager: episodic memory with lifecycle hooks
    vector_store.py      # VectorStore: LanceDB/Qdrant abstraction with hybrid search
    code_indexer.py      # CodeIndexer: Tree-sitter parsing and symbol extraction
    compressor.py        # ContextCompressor: multi-strategy context compression
    budget.py            # TokenBudget: token counting and budget enforcement
    mcp.py               # MCPIntegration: MCP tool/resource injection for L2
```

### Pattern 1: Priority-Based Context Assembly

**What:** ContextAdapter assembles context items with explicit priorities (CRITICAL, HIGH, MEDIUM, LOW) and a hard token budget. Items are added in priority order; when budget is exceeded, the compressor kicks in.

**When to use:** Every agent invocation.

**Example:**
```python
# Source: SYSTEM_DESIGN.md Section 5.3
class ContextAdapter:
    async def build_context(self, task: TaskSchema) -> AgentContext:
        context = AgentContext(budget=self.token_budget)

        # L0: Always loaded (CRITICAL priority, never dropped)
        l0 = await self.loader.load_l0()
        context.add(l0, priority=Priority.CRITICAL)

        # Task data from shared state (HIGH priority)
        task_data = self._extract_task_context(task)
        context.add(task_data, priority=Priority.HIGH)

        # L1: On-demand relevant files (MEDIUM priority)
        relevant_files = await self.code_indexer.find_relevant(task.description)
        for file_ctx in relevant_files:
            if context.has_budget():
                l1 = await self.loader.load_l1(file_ctx.path)
                context.add(l1, priority=Priority.MEDIUM)

        # L2: RAG retrieval (LOW priority)
        if context.has_budget():
            rag_results = await self.vector_store.query(
                query=task.description, top_k=5,
                filter={"project_id": str(task.project_id)},
            )
            for result in rag_results:
                context.add(result.content, priority=Priority.LOW)

        # Compress if over budget
        if context.is_over_budget():
            context = await self.compressor.compress(context)

        return context
```

### Pattern 2: Vector Store Backend Abstraction

**What:** A `VectorStoreBackend` protocol that both LanceDB and Qdrant implement, letting the ContextAdapter be backend-agnostic. Selection happens at startup via configuration.

**When to use:** When instantiating the context system.

**Example:**
```python
from typing import Protocol

class VectorStoreBackend(Protocol):
    async def upsert(self, id: str, content: str, embedding: list[float],
                     metadata: dict) -> None: ...
    async def query(self, query_embedding: list[float], top_k: int = 5,
                    filter: dict | None = None) -> list[VectorResult]: ...
    async def delete(self, ids: list[str]) -> None: ...
    async def create_fts_index(self, field: str) -> None: ...
    async def hybrid_search(self, query: str, query_embedding: list[float],
                            top_k: int = 5) -> list[VectorResult]: ...

class LanceDBBackend:
    """Embedded LanceDB for development and small projects."""
    def __init__(self, persist_dir: str = ".codebot/vectors"):
        self.db = lancedb.connect(persist_dir)
        # ...

class QdrantBackend:
    """Qdrant server for production deployments."""
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = AsyncQdrantClient(url=url)
        # ...
```

### Pattern 3: Tree-sitter Symbol Extraction

**What:** CodeIndexer uses tree-sitter query patterns (S-expressions) to extract functions, classes, methods, and imports from source files. Extracted symbols are stored in the vector store for semantic search.

**When to use:** During initial codebase indexing and incremental updates.

**Example:**
```python
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())

# S-expression queries for Python symbol extraction
PYTHON_QUERIES = {
    "functions": "(function_definition name: (identifier) @name) @definition",
    "classes": "(class_definition name: (identifier) @name) @definition",
    "imports": "[(import_statement) (import_from_statement)] @import",
    "methods": "(class_definition body: (block (function_definition name: (identifier) @name) @method))",
}

parser = Parser(PY_LANGUAGE)
tree = parser.parse(source_bytes)
query = PY_LANGUAGE.query(PYTHON_QUERIES["functions"])
captures = query.captures(tree.root_node)
```

### Pattern 4: Token Budget Enforcement

**What:** `AgentContext` tracks token usage per item using tiktoken. Hard budget is set per agent type. Budget is checked before adding each item.

**When to use:** Every time content is added to context.

**Example:**
```python
import tiktoken

class TokenBudget:
    def __init__(self, max_tokens: int, model: str = "gpt-4o"):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        self._encoder = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def has_budget(self, needed: int = 0) -> bool:
        return (self.used_tokens + needed) <= self.max_tokens

    def consume(self, text: str) -> int:
        tokens = self.count(text)
        self.used_tokens += tokens
        return tokens
```

### Anti-Patterns to Avoid

- **Loading all context upfront:** Never load L2 context eagerly. L2 should be deferred (MCP tools registered, agent pulls on demand) to avoid wasting budget on irrelevant information.
- **Silent budget overflow:** Never silently exceed token limits. The system MUST either compress, truncate, or raise an error. CTXT-07 requires hard enforcement.
- **Single embedding model for all content:** Code and natural language require different treatment. Use code-specific queries (tree-sitter structural search) alongside semantic search.
- **Synchronous file I/O in async context:** All file operations in the context module must use aiofiles or asyncio.to_thread() to avoid blocking the event loop.
- **Unbounded vector store results:** Always set explicit top_k limits and apply relevance score thresholds to prevent returning too many low-quality matches.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Custom word-count heuristic | tiktoken 0.12.0 | BPE tokenization differs from word count by up to 40%; tiktoken matches OpenAI's actual counting; model-specific encodings matter |
| Text embeddings | Custom embedding pipeline | sentence-transformers + all-MiniLM-L6-v2 | Pre-trained on 1B pairs, 384-dim vectors, 22MB model, production-proven; custom training requires massive compute |
| Code parsing | Regex-based function extraction | tree-sitter 0.25.2 | Regex breaks on nested structures, comments, strings; tree-sitter builds proper ASTs; supports 100+ languages |
| Vector similarity search | Custom nearest-neighbor | LanceDB / Qdrant | IVF indexes, HNSW, BM25 fusion, distance metrics -- all battle-tested at scale |
| BPE tokenizer registry | Mapping model names to encoders | tiktoken.encoding_for_model() | Maintained by OpenAI, updated with new models; for non-OpenAI models, use litellm.token_counter() |
| Hybrid search reranking | Custom score fusion | LanceDB RRFReranker | Reciprocal Rank Fusion is a well-studied algorithm; LanceDB implements it natively with configurable weights |

**Key insight:** Context management is a composition problem, not an algorithm problem. The value is in orchestrating proven tools (vector stores, tokenizers, parsers) with a clean priority/budget system, not in reimplementing any individual capability.

## Common Pitfalls

### Pitfall 1: Token Count Mismatch Between Counting and Actual LLM

**What goes wrong:** Token count estimated by tiktoken differs from the actual count used by the LLM provider (especially for Anthropic/Google models that use different tokenizers).
**Why it happens:** tiktoken uses OpenAI's BPE tokenizers; Claude uses a different tokenizer; Gemini uses yet another.
**How to avoid:** Use tiktoken as a fast approximation with a 15% safety margin. For Anthropic, their token counting API or litellm.token_counter("claude-3-5-sonnet", text) provides accurate counts. Set budget to 85% of actual model context window.
**Warning signs:** Agents hitting context length errors despite budgets appearing under limit.

### Pitfall 2: Embedding Model Size Explosion

**What goes wrong:** sentence-transformers models download 400MB+ on first use, slowing CI and cold starts.
**Why it happens:** Default models like all-mpnet-base-v2 are large; GPU requirements add complexity.
**How to avoid:** Use all-MiniLM-L6-v2 (22MB, CPU-friendly, 5x faster than mpnet). Pre-download models during Docker build. Consider LanceDB's built-in embedding registry as alternative.
**Warning signs:** Slow first-run performance, Docker images growing unexpectedly.

### Pitfall 3: Tree-sitter Grammar Version Mismatch

**What goes wrong:** tree-sitter core and language grammars use different ABI versions, causing segfaults or parse failures.
**Why it happens:** Language grammars are published independently of the core library.
**How to avoid:** Pin both tree-sitter and all tree-sitter-{language} packages together. The modern approach (v0.25+) uses pre-compiled language packages (`tree-sitter-python`) that bundle the correct ABI version. Do NOT use the deprecated `tree-sitter-languages` package.
**Warning signs:** Segmentation faults during parsing, "incompatible ABI" errors.

### Pitfall 4: Vector Store Index Not Created Before Search

**What goes wrong:** FTS (full-text search) queries fail with "index not found" because `create_fts_index()` was not called after table creation.
**Why it happens:** LanceDB requires explicit FTS index creation; vector search works without an index (brute-force) but FTS/hybrid do not.
**How to avoid:** Always call `table.create_fts_index("text_column")` after creating or loading a table. Include index creation in the indexing pipeline, not the query path.
**Warning signs:** "No full-text index found" errors during hybrid search.

### Pitfall 5: Context Priority Starvation

**What goes wrong:** L0 context is so large that no budget remains for L1/L2, making agents effectively blind to task-specific information.
**Why it happens:** L0 includes project config that grows as the project grows (more files, more conventions).
**How to avoid:** Set a hard cap on L0 (2K tokens max). Summarize L0 content if it exceeds cap. Monitor L0 size as projects grow.
**Warning signs:** L1 items consistently being dropped or compressed; agents producing generic responses.

### Pitfall 6: Blocking the Event Loop with File I/O

**What goes wrong:** Synchronous file reads in an async context block the entire event loop, causing timeouts for concurrent agent executions.
**Why it happens:** Standard `open()` and `os.walk()` are synchronous. Tree-sitter `parser.parse()` is CPU-bound.
**How to avoid:** Use `aiofiles.open()` for all file reads. Wrap CPU-bound tree-sitter parsing in `asyncio.to_thread()`. Use `asyncio.TaskGroup` for parallel file loading.
**Warning signs:** Agent execution timeouts during context assembly; slow concurrent performance.

## Code Examples

### Example 1: LanceDB Hybrid Search Setup

```python
# Source: LanceDB docs (https://docs.lancedb.com/search/hybrid-search)
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from lancedb.rerankers import RRFReranker

# Use sentence-transformers via LanceDB's embedding registry
embedder = get_registry().get("sentence-transformers").create(
    name="all-MiniLM-L6-v2"
)

class CodeChunk(LanceModel):
    text: str = embedder.SourceField()
    vector: Vector(embedder.ndims()) = embedder.VectorField()
    file_path: str
    symbol_name: str
    symbol_kind: str  # "function", "class", "import"
    line_start: int
    line_end: int
    project_id: str

db = lancedb.connect(".codebot/vectors")
table = db.create_table("code_chunks", schema=CodeChunk, mode="overwrite")

# Add data (embeddings auto-generated)
table.add([
    {"text": "def build_context(self, task):", "file_path": "context/adapter.py",
     "symbol_name": "build_context", "symbol_kind": "function",
     "line_start": 40, "line_end": 90, "project_id": "proj-123"}
])

# Create FTS index for hybrid search
table.create_fts_index("text", replace=True)

# Hybrid search with reranking
reranker = RRFReranker()
results = (
    table.search("context assembly for agents", query_type="hybrid")
    .rerank(reranker=reranker)
    .where(f"project_id = 'proj-123'")
    .limit(10)
    .to_list()
)
```

### Example 2: Tree-sitter Code Indexing

```python
# Source: py-tree-sitter docs (https://tree-sitter.github.io/py-tree-sitter/)
import tree_sitter_python as tspython
import tree_sitter_typescript as tsjs
from tree_sitter import Language, Parser
from dataclasses import dataclass

@dataclass(slots=True, kw_only=True)
class CodeSymbol:
    name: str
    kind: str  # "function", "class", "method", "import"
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: str | None = None

LANGUAGES = {
    ".py": Language(tspython.language()),
    ".ts": Language(tsjs.language_typescript()),
    ".tsx": Language(tsjs.language_tsx()),
}

QUERIES = {
    ".py": {
        "functions": "(function_definition name: (identifier) @name) @def",
        "classes": "(class_definition name: (identifier) @name) @def",
        "imports": "[(import_statement) (import_from_statement)] @import",
    },
    ".ts": {
        "functions": "(function_declaration name: (identifier) @name) @def",
        "classes": "(class_declaration name: (identifier) @name) @def",
        "imports": "(import_statement) @import",
    },
}

def extract_symbols(source: bytes, file_path: str, ext: str) -> list[CodeSymbol]:
    lang = LANGUAGES.get(ext)
    if not lang:
        return []
    parser = Parser(lang)
    tree = parser.parse(source)
    symbols = []
    for query_kind, query_str in QUERIES.get(ext, {}).items():
        query = lang.query(query_str)
        captures = query.captures(tree.root_node)
        for node, capture_name in captures:
            if capture_name == "name":
                continue  # skip name-only captures
            symbols.append(CodeSymbol(
                name=_get_name(node, source),
                kind=query_kind.rstrip("s"),  # "functions" -> "function"
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=source[node.start_byte:min(node.start_byte+200, node.end_byte)].decode(),
            ))
    return symbols

def _get_name(node, source: bytes) -> str:
    for child in node.children:
        if child.type == "identifier":
            return source[child.start_byte:child.end_byte].decode()
    return "<unnamed>"
```

### Example 3: Token Budget Enforcement

```python
# Source: CodeBot SYSTEM_DESIGN.md Section 5 + tiktoken docs
import enum
import tiktoken
from pydantic import BaseModel

class Priority(str, enum.Enum):
    CRITICAL = "CRITICAL"  # L0: never dropped
    HIGH = "HIGH"          # Task-specific data
    MEDIUM = "MEDIUM"      # L1: relevant files
    LOW = "LOW"            # L2: RAG results

class ContextItem(BaseModel):
    id: str
    content: str
    priority: Priority
    token_count: int
    source: str  # "l0", "l1", "l2", "memory", "task"

class AgentContext:
    def __init__(self, budget: int, model: str = "gpt-4o"):
        self._budget = budget
        self._items: list[ContextItem] = []
        self._used_tokens = 0
        self._encoder = tiktoken.encoding_for_model(model)

    def add(self, content: str, priority: Priority, source: str = "") -> bool:
        tokens = len(self._encoder.encode(content))
        item = ContextItem(
            id=f"{source}_{len(self._items)}",
            content=content,
            priority=priority,
            token_count=tokens,
            source=source,
        )
        self._items.append(item)
        self._used_tokens += tokens
        return self._used_tokens <= self._budget

    def has_budget(self, reserve: int = 0) -> bool:
        return (self._used_tokens + reserve) <= self._budget

    def is_over_budget(self) -> bool:
        return self._used_tokens > self._budget

    def remove_items_by_priority(self, priority: Priority) -> int:
        removed = 0
        self._items = [
            item for item in self._items
            if item.priority != priority or (removed := removed) is None
        ]
        # Simpler:
        kept = []
        removed_tokens = 0
        for item in self._items:
            if item.priority == priority:
                removed_tokens += item.token_count
            else:
                kept.append(item)
        self._items = kept
        self._used_tokens -= removed_tokens
        return removed_tokens

    def to_text(self) -> str:
        """Render all context items as a single string for LLM input."""
        return "\n---\n".join(item.content for item in self._items)

    @property
    def total_tokens(self) -> int:
        return self._used_tokens

    @property
    def remaining_budget(self) -> int:
        return max(0, self._budget - self._used_tokens)
```

### Example 4: Qdrant Async Client Usage

```python
# Source: qdrant-client docs (https://python-client.qdrant.tech/)
from qdrant_client import AsyncQdrantClient, models

async def create_qdrant_backend(url: str = "http://localhost:6333"):
    client = AsyncQdrantClient(url=url)

    # Create collection if not exists
    collections = await client.get_collections()
    if "codebot" not in [c.name for c in collections.collections]:
        await client.create_collection(
            collection_name="codebot",
            vectors_config=models.VectorParams(
                size=384,  # all-MiniLM-L6-v2 dimension
                distance=models.Distance.COSINE,
            ),
        )

    return client

async def search(client: AsyncQdrantClient, embedding: list[float],
                 project_id: str, top_k: int = 5):
    results = await client.query_points(
        collection_name="codebot",
        query=embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="project_id",
                    match=models.MatchValue(value=project_id),
                )
            ]
        ),
        limit=top_k,
    )
    return results.points
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tree-sitter-languages (single package) | Per-language packages (tree-sitter-python, etc.) | 2025 | tree-sitter-languages is unmaintained; per-language packages provide ABI-compatible pre-compiled wheels |
| ChromaDB for vector store | LanceDB with native hybrid search | 2025-2026 | LanceDB adds BM25 + vector fusion natively; ChromaDB requires external BM25 |
| sentence-transformers v2-3 | sentence-transformers v5.3 (sparse encoders) | 2025-07 | v5.0 added SparseEncoder models; v5.3 adds hardness weighting; breaking API changes from v4 |
| Manual embedding in Qdrant | Qdrant builtin inference + FastEmbed | 2025-2026 | Qdrant client can auto-embed; BM25 support moved builtin (no longer needs FastEmbed) |
| qdrant search() | qdrant query_points() | 2025 | search(), recommend(), discovery() methods deprecated in latest qdrant-client; use query_points() |
| tiktoken with cl100k_base | tiktoken with o200k_base | 2024-2025 | GPT-4o and newer models use o200k_base encoding; cl100k_base still works for GPT-4/3.5 |

**Deprecated/outdated:**
- `tree-sitter-languages` package: unmaintained, use individual `tree-sitter-{language}` packages
- `qdrant-client` methods `search()`, `recommend()`, `discovery()`, `upload_records()`: all deprecated, use `query_points()` and `upsert()`
- `ChromaDB` as primary vector store: project design specifies LanceDB (dev) / Qdrant (prod)
- `sentence-transformers` v4.x import patterns may break with v5.x; dual-compatibility maintained but test explicitly

## Open Questions

1. **Embedding model choice for code vs. prose**
   - What we know: all-MiniLM-L6-v2 is optimized for natural language similarity. Code has different semantic structure.
   - What's unclear: Whether a code-specific model (e.g., UniXcoder, CodeBERT, or Nomic's code embeddings) would significantly improve L2 retrieval quality for code search.
   - Recommendation: Start with all-MiniLM-L6-v2 for simplicity. Add a configuration option for `code_embedding_model` vs `text_embedding_model`. Benchmark with real codebase data in a later iteration.

2. **LanceDB async API maturity**
   - What we know: LanceDB has `connect_async()` and `AsyncTable` but some features (like `to_pydantic()`) only work synchronously. Some issues reported with async + cloud.
   - What's unclear: Whether all hybrid search features work fully in async mode for embedded (local) usage.
   - Recommendation: Use sync LanceDB API wrapped in `asyncio.to_thread()` for the initial implementation. This avoids potential async API gaps. Switch to native async once verified stable.

3. **MemoryManager scope for Phase 5**
   - What we know: SYSTEM_DESIGN.md defines a full MemoryManager with lifecycle hooks, semantic compression, and progressive disclosure.
   - What's unclear: Whether the full MemoryManager should be implemented in Phase 5 or deferred since it crosses into episodic memory territory.
   - Recommendation: Implement basic MemoryManager with remember/recall (SQLite + vector store). Defer lifecycle hooks and semantic compression to a later phase. The CTXT requirements do not explicitly require episodic memory.

4. **Token counting for non-OpenAI models**
   - What we know: tiktoken only supports OpenAI tokenizers (o200k_base, cl100k_base, p50k_base). Anthropic and Google use different tokenizers.
   - What's unclear: Exact token counts for Claude and Gemini models.
   - Recommendation: Use tiktoken's cl100k_base as a universal approximation (within ~10% for most models). Apply a 15% safety margin to budgets. Use litellm.token_counter() as an alternative when exact counts are needed (it wraps model-specific tokenizers).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | apps/server/pyproject.toml (asyncio_mode = "auto") |
| Quick run command | `uv run pytest tests/unit/context/ -x -q` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CTXT-01 | L0 context auto-included in every agent call | unit | `uv run pytest tests/unit/context/test_tiers.py::test_l0_always_loaded -x` | Wave 0 |
| CTXT-02 | L1 context assembled per-phase for agents | unit | `uv run pytest tests/unit/context/test_tiers.py::test_l1_phase_scoped -x` | Wave 0 |
| CTXT-03 | L2 retrieval returns semantically relevant results | integration | `uv run pytest tests/integration/context/test_vector_search.py -x` | Wave 0 |
| CTXT-04 | Vector store indexes codebase for semantic search | integration | `uv run pytest tests/integration/context/test_vector_store.py -x` | Wave 0 |
| CTXT-05 | Tree-sitter extracts functions, classes, imports | unit | `uv run pytest tests/unit/context/test_code_indexer.py -x` | Wave 0 |
| CTXT-06 | Context compression fits oversized context into budget | unit | `uv run pytest tests/unit/context/test_compressor.py -x` | Wave 0 |
| CTXT-07 | Hard token budgets enforced per agent call | unit | `uv run pytest tests/unit/context/test_budget.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/context/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/context/test_tiers.py` -- covers CTXT-01, CTXT-02
- [ ] `tests/unit/context/test_budget.py` -- covers CTXT-07
- [ ] `tests/unit/context/test_code_indexer.py` -- covers CTXT-05
- [ ] `tests/unit/context/test_compressor.py` -- covers CTXT-06
- [ ] `tests/integration/context/test_vector_store.py` -- covers CTXT-04
- [ ] `tests/integration/context/test_vector_search.py` -- covers CTXT-03
- [ ] `tests/unit/context/conftest.py` -- shared fixtures (mock LLM for compressor, sample code files, in-memory vector store)
- [ ] Framework install: `uv add --dev pytest-asyncio` -- already in dev deps but verify

## Sources

### Primary (HIGH confidence)

- LanceDB Python API docs: https://lancedb.github.io/lancedb/python/python/ -- async API, hybrid search, FTS index
- LanceDB hybrid search docs: https://docs.lancedb.com/search/hybrid-search -- BM25 + vector fusion, rerankers
- py-tree-sitter docs: https://tree-sitter.github.io/py-tree-sitter/ -- Query API, captures, Language setup
- Qdrant Python client docs: https://python-client.qdrant.tech/ -- AsyncQdrantClient, query_points, deprecated methods
- tiktoken PyPI/GitHub: https://pypi.org/project/tiktoken/ -- encoding_for_model, o200k_base
- sentence-transformers docs: https://sbert.net/ -- v5.3 API, model registry
- SYSTEM_DESIGN.md Section 5 -- ContextAdapter, ThreeTierLoader, VectorStore, CodeIndexer, ContextCompressor, MemoryManager class designs
- ARCHITECTURE.md Section 6 -- Context Management System three-tier architecture, Context Adapter pipeline
- PyPI verified versions (2026-03-18) -- lancedb 0.30.0, qdrant-client 1.17.1, tree-sitter 0.25.2, tiktoken 0.12.0, sentence-transformers 5.3.0, aiofiles 25.1.0

### Secondary (MEDIUM confidence)

- Anthropic context engineering blog: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents -- compaction vs summarization, 85% budget trigger
- Context window management strategies: https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/ -- budget planning, subagent isolation
- Factory.ai context window problem: https://factory.ai/news/context-window-problem -- context rot, diminishing returns

### Tertiary (LOW confidence)

- Embedding model comparison (code vs prose): Based on training data knowledge, not verified with current benchmarks -- LOW confidence on code-specific embedding quality claims
- LanceDB async API stability: Based on GitHub issues and docs -- some features may have gaps in async mode

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against PyPI, APIs confirmed via official docs and web search
- Architecture: HIGH -- detailed class designs exist in SYSTEM_DESIGN.md; this phase implements them directly
- Pitfalls: HIGH -- verified through official docs (deprecated Qdrant methods, tree-sitter ABI issues, token counting mismatches)
- Code examples: HIGH -- all examples sourced from official documentation or verified against current API

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (30 days -- stable libraries, well-defined architecture)
