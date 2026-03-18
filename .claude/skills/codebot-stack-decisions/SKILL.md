---
name: codebot-stack-decisions
description: |
  Technology selection decisions for the CodeBot multi-agent SDLC platform. USE THIS
  SKILL whenever choosing technologies, evaluating alternatives, checking version
  compatibility, or avoiding wrong tech choices. Covers recommended stack, alternatives
  considered, what NOT to use, version compatibility matrix, and deployment variants.
  Trigger for: tech stack questions, "should we use X", dependency selection, version
  conflicts, deployment environment configuration.
---

# CodeBot Technology Stack Decisions

## Core Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | Python | 3.12+ | Primary runtime (agents, orchestration, API) |
| **API** | FastAPI | >=0.115.0 | HTTP + WebSocket, OpenAPI generation |
| **Validation** | Pydantic | >=2.9.0 | Data validation, settings, LLM output parsing |
| **Graph Engine** | LangGraph | >=0.2.x | DAG execution with cycles, checkpointing |
| **Durable Workflows** | Temporal | >=1.x (Python SDK) | Long-running pipeline durability |
| **LLM Gateway** | LiteLLM | >=1.82.0 | Unified gateway for 100+ providers, cost tracking |
| **LLM Routing** | RouteLLM | latest | Cost-quality model routing (30-50% cost reduction) |
| **Event Bus** | NATS JetStream | latest | Sub-ms pub/sub, at-least-once delivery |
| **Database** | PostgreSQL | >=16 | Pipeline state, checkpoints, user data |
| **Cache** | Redis | >=5.2.0 | Session cache, rate limiting, ephemeral state |
| **Vector (dev)** | LanceDB | >=0.15.0 | Embedded vector DB, hybrid search |
| **Vector (prod)** | Qdrant | >=1.12.0 | Distributed vector DB, horizontal scaling |
| **Analytics** | DuckDB | latest | In-process OLAP for cost analytics |
| **ORM** | SQLAlchemy | >=2.0.35 | Async ORM with MappedColumn type safety |
| **Dashboard** | React + Vite | React >=18.3, Vite >=6.0 | SPA dashboard |
| **TypeScript** | TypeScript | >=5.5.0 | Strict mode, ESM only |
| **Styling** | Tailwind CSS | >=4.0.0 | Utility-first, CSS variables native |
| **UI Components** | Shadcn/ui | latest | Accessible, Radix-based, copy-paste pattern |
| **Graph Viz** | React Flow | latest | DAG visualization with ELKjs layout |
| **State** | Zustand | >=5.0.0 | Client state (30 concurrent agent updates) |
| **Server State** | TanStack Query | >=5.60.0 | Declarative data fetching with SWR |
| **Real-time** | Socket.IO | latest | WebSocket with auto-reconnection, rooms |
| **CLI** | Node.js | 22.x LTS | CLI runtime |
| **Monorepo** | Turborepo | latest | Cached builds, workspace-aware |
| **Python Pkg** | uv | latest | 10-100x faster than pip, Rust resolver |
| **Node Pkg** | pnpm | >=9.x | Strict, symlink-based, no hoisting issues |

---

## What NOT to Use

These are technologies that seem appealing but create problems in this architecture.

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Flask / Django | Synchronous; Django ORM incompatible with asyncio TaskGroup; no auto OpenAPI | FastAPI |
| Celery | Sync worker model; no durable execution semantics for hour-long pipelines | Temporal + Taskiq |
| ChromaDB | Performance degrades above ~1M vectors; no native hybrid search | LanceDB (dev) / Qdrant (prod) |
| Pinecone / Weaviate Cloud | Hosted services expose generated code to third parties | Self-hosted Qdrant |
| Webpack / Create React App | CRA archived 2023; Webpack 5-20x slower than Vite | Vite |
| Redux Toolkit | Excessive boilerplate; 30 concurrent agent updates cause perf issues | Zustand |
| OpenRouter | Hosted LLM proxy; code sent to third-party | LiteLLM (self-hosted) |
| Poetry | Slow pure-Python resolver; non-standard lockfile | uv |
| Flake8 + Black + isort | Three tools, three configs, three CI steps | ruff (all-in-one) |
| SQLite in production | Concurrent writes from 30+ agents serialize; no connection pooling | PostgreSQL + asyncpg |
| LangChain as graph engine | Chain composition library, not a graph engine | LangGraph (built on LangChain) |
| Kafka | Operationally heavy (ZooKeeper/KRaft); overkill for CodeBot throughput | NATS JetStream |
| RabbitMQ | Lacks streaming semantics for agent event replay | NATS JetStream |
| Next.js | SSR/RSC complexity unnecessary for real-time WebSocket dashboard | Vite SPA |
| Material UI | Heavy default look requiring effort to customize | Shadcn/ui + Tailwind |
| ESLint + Prettier | Two tools with occasional conflicts | Biome (single Rust binary, 35x faster) |

### Deferred to v2 (Not Wrong, Just Not Now)

| Technology | Why Deferred |
|-----------|-------------|
| Aider / Continue CLI | Claude Code + Codex + Gemini CLI cover v1 needs |
| vLLM / LocalAI / TGI | Ollama and LM Studio cover self-hosted v1 needs |
| CRDT (Yjs) | Agents use worktree isolation; no human+agent co-editing in v1 |
| Native iOS (Swift) / Android (Kotlin) | React Native covers cross-platform mobile |
| Flutter | Out of scope per project requirements |

---

## Alternatives Considered

For each core choice, the alternative that came closest and when you'd pick it instead:

| Recommended | Runner-up | When to Use Runner-up |
|-------------|-----------|----------------------|
| LangGraph | CrewAI | Simpler role-based agent teams without cyclical debug loops |
| LangGraph | AutoGen | Conversational multi-agent patterns (group chat model) |
| Temporal | Celery + Redis | Simple task queues without hour-long durable execution |
| LiteLLM | OpenRouter | When data leaving your infrastructure is acceptable |
| NATS JetStream | Kafka | When you need massive throughput (100K+ msg/sec) |
| LanceDB | ChromaDB | Small projects under 100K vectors with simple similarity search |
| Qdrant (prod) | Weaviate | Both strong; Weaviate if you need GraphQL-native queries |
| Vite | Next.js | When you need SSR/RSC for SEO (not applicable to dashboard) |
| Turborepo | Nx | Steeper learning curve but more features for very large monorepos |
| Pulumi | Terraform/OpenTofu | When team prefers HCL or has existing Terraform state |
| pytest | unittest | Never — pytest is strictly superior for async agent testing |

---

## Version Compatibility Matrix

These combinations are tested together. Do not mix incompatible versions.

| Package | Compatible With | Critical Notes |
|---------|----------------|---------------|
| Python 3.12.x | SQLAlchemy >=2.0.35, FastAPI >=0.115.0, Pydantic >=2.9.0 | asyncio.TaskGroup requires 3.11+; use 3.12 for perf |
| LangGraph >=0.2.x | langchain-core >=0.3.0 | LangGraph 0.2+ dropped pre-0.2 API |
| FastAPI >=0.115.0 | Pydantic v2 only | Dropped Pydantic v1 compatibility |
| SQLAlchemy 2.0 async | asyncpg >=0.30.0, aiosqlite >=0.20.0 | Do NOT use psycopg2 (sync driver) |
| Vite >=6.0.0 | React >=18.3.0, TypeScript >=5.5.0 | Requires Node >=18; use Node 22 LTS |
| TailwindCSS >=4.0.0 | PostCSS >=8.x | No longer requires tailwind.config.js |
| React Router >=7.0.0 | React >=18.3.0 | Breaking changes from v6 (merged Remix API) |
| Temporalio Python SDK | Python >=3.9, Temporal server >=1.24 | Async-native |
| LiteLLM >=1.82.0 | anthropic >=0.39.0, openai >=1.55.0, google-genai >=1.0.0 | Keep provider SDKs matched |
| LanceDB >=0.15.0 | lancedb Python package only | Not compatible with ChromaDB APIs |

---

## Stack Patterns by Deployment Variant

### Local Development (Single Developer)

```yaml
database: SQLite (aiosqlite) — zero-config
vector: LanceDB embedded — no separate server
cache: Redis via Docker
events: NATS via Docker
llm: Ollama for local models (avoid API costs)
durability: LangGraph checkpointing only (skip Temporal)
docker-compose: Redis, NATS, LiteLLM proxy, SigNoz
```

### Production (Cloud, Multi-User)

```yaml
database: PostgreSQL 16 (RDS or self-hosted with replication)
vector: Qdrant cluster (3-node minimum for HA)
cache: Redis cluster or ElastiCache
events: NATS cluster with JetStream replication factor 3
durability: Temporal cluster (3-node minimum)
llm: LiteLLM proxy as dedicated service
observability: SigNoz or Prometheus + Grafana + Jaeger
```

### Air-Gapped / Privacy-First

```yaml
llm: Ollama for all inference (Llama 3, DeepSeek, Qwen)
database: All self-hosted (PostgreSQL, Redis, Qdrant)
gateway: LiteLLM proxy routing 100% to Ollama
security: Semgrep/Trivy/Gitleaks run locally (no external services)
```

---

## LLM Provider Strategy

### Path 1 — API Providers (via LLM Gateway)

| Provider | SDK | Best For | Models |
|----------|-----|----------|--------|
| Anthropic | anthropic >=0.39.0 | Architecture, planning, code review | Opus 4.6, Sonnet 4, Haiku 3.5 |
| OpenAI | openai >=1.55.0 | Reasoning, analysis | GPT-4.1, o3, o4-mini |
| Google | google-genai >=1.0.0 | Long-context analysis (1M+ tokens), research | Gemini 2.5 Pro, 2.5 Flash |
| Ollama | local HTTP | Privacy-sensitive, offline, development | Llama 3, Mistral, CodeLlama, Qwen, DeepSeek |
| LM Studio | local HTTP | Desktop local model testing | GUI-based model management |

### Path 2 — CLI Agents (Direct Integration, bypass gateway)

| Agent | Integration | Best For | Key Capability |
|-------|------------|----------|----------------|
| Claude Code | Agent SDK (in-process) | S5 Implementation, S8 Debug | Built-in tools, subagents, MCP, session resume |
| OpenAI Codex CLI | Subprocess | S5 Tests, S7 Testing | Approval modes, auto-edit, full-auto |
| Google Gemini CLI | Subprocess | S2 Research | 1M+ token context, sandbox modes |

**Two execution paths:**
- **Path 1 — LLM Gateway (API reasoning):** All API-based providers are accessed through
  the LiteLLM proxy. RouteLLM dynamically routes easy tasks to cheaper models, reducing
  LLM spend by 30-50%.
- **Path 2 — Direct CLI Agent Integration (autonomous coding):** Claude Code (Agent SDK,
  in-process), OpenAI Codex CLI (subprocess), and Google Gemini CLI (subprocess) integrate
  directly with the platform — they bypass the LLM gateway entirely. These are full
  autonomous coding agents, not API wrappers.

---

## Observability Stack

| Tool | Purpose | When to Use |
|------|---------|-------------|
| OpenTelemetry | Distributed tracing across all agents | Always — instruments FastAPI, SQLAlchemy, httpx |
| Langfuse | LLM observability and cost tracking per agent | Always — integrates with LiteLLM via callback |
| SigNoz | All-in-one traces + metrics + logs | Simpler ops (replaces separate Jaeger + Prometheus + Grafana) |
| Prometheus + Grafana | Platform metrics and dashboards | When you need more dashboard customization than SigNoz |
| Sentry (self-hosted) | Exception tracking across 30 agents | Always — self-hosted to avoid code exfiltration |

---

## Quick Decision Reference

| "Should I use...?" | Answer |
|--------------------|--------|
| ChromaDB for vectors? | No — use LanceDB (dev) or Qdrant (prod) |
| Django for the backend? | No — use FastAPI (async-first, auto OpenAPI) |
| Redux for dashboard state? | No — use Zustand (less boilerplate, better perf) |
| Poetry for Python deps? | No — use uv (10-100x faster) |
| Kafka for the event bus? | No — use NATS JetStream (simpler, sub-ms latency) |
| Next.js for the dashboard? | No — Vite SPA (dashboard is real-time WebSocket, not SSR) |
| OpenAI API directly from agents? | No — API calls go through LiteLLM proxy |
| Claude Code / Codex / Gemini CLI through LiteLLM? | No — CLI agents integrate directly, bypassing the gateway |
| Celery for task queues? | No — use Temporal for durable workflows |
| ESLint + Prettier? | No — use Biome (single binary, 35x faster) |
| psycopg2 for PostgreSQL? | No — use asyncpg (async driver required for SQLAlchemy 2.0 async) |

## Documentation Lookup (Context7)

When evaluating technologies or verifying version compatibility, use Context7 to fetch current docs:

```
# Resolve any library from the stack:
mcp__plugin_context7_context7__resolve-library-id("<library-name>")
mcp__plugin_context7_context7__query-docs(id, "<specific question about API, config, or migration>")
```

This is critical when:
- Checking if a feature exists in the pinned version (e.g., does LangGraph 0.2.x support subgraph composition?)
- Verifying migration paths (Pydantic v1→v2, SQLAlchemy 1.x→2.0, Tailwind 3→4)
- Evaluating alternative libraries by querying their current API surfaces
- Confirming dependency compatibility between pinned versions
