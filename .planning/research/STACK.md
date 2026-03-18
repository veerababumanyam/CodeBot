# Technology Stack

**Project:** CodeBot -- Autonomous Multi-Agent SDLC Platform
**Researched:** 2026-03-18
**Overall Confidence:** HIGH

---

## Recommended Stack

This document prescribes the full technology stack for CodeBot. Choices are informed by the existing monorepo foundation (Turborepo, uv, pnpm, Docker Compose with PostgreSQL/Redis/NATS already running), the architecture documents (v2.5), and current ecosystem research as of March 2026.

---

### 1. Core Languages & Runtime

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **Python** | 3.12+ | Backend, orchestration, agents, graph engine | Dominant language for AI/ML tooling. LangGraph, Temporal, LiteLLM, LlamaIndex all Python-first. Strict mypy + ruff provides safety. 3.12 has TaskGroup, ExceptionGroup. | HIGH |
| **TypeScript** | 5.5+ | Dashboard, CLI, shared types | Strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`. ESM only. Industry standard for React + Vite. | HIGH |
| **Node.js** | 22 LTS | Runtime for dashboard/CLI | Current LTS. Required by Vite, React, Turborepo. | HIGH |
| **Rust** (indirect) | -- | Via tree-sitter, ast-grep, LanceDB, Qdrant | Not written directly, but several critical dependencies are Rust-native, giving us C-level performance for parsing and search. | HIGH |

### 2. Web Framework (Backend)

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **FastAPI** | 0.135+ | REST API, WebSocket, SSE | 96K GitHub stars. Async-native, Pydantic v2 integration, automatic OpenAPI docs. Already in `pyproject.toml`. Mature and stable -- the standard Python API framework. | HIGH |
| **Uvicorn** | 0.30+ | ASGI server | Standard FastAPI server. Already a dependency. | HIGH |
| **Pydantic** | 2.9+ | Validation, serialization, settings | Core to FastAPI. v2 is 5-50x faster than v1. Already in use for shared models in `libs/agent-sdk/`. | HIGH |
| **Pydantic Settings** | 2.5+ | Configuration management | 12-factor config from env vars. Already a dependency. | HIGH |

**NOT recommended:** Django/Flask (synchronous-first, heavier ORM coupling), Litestar (smaller ecosystem, less LLM tooling integration).

### 3. Agent Graph Engine

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **LangGraph** | 1.0+ (stable) | Stateful agent graph execution | Hit v1.0 in October 2025 with stability commitment. 24.6K stars, MIT. Native directed graph execution, durable state persistence, human-in-the-loop, checkpoint/resume, node-level caching (May 2025), dynamic tool calling (Aug 2025), MCP streamable HTTP transport. Used by Uber, LinkedIn, Klarna. `create_agent` is now the standard API. Dropped Python 3.9 support. | HIGH |
| **Temporal** | Python SDK 1.4+ | Durable workflow orchestration | 18.9K stars, MIT. Retry/checkpoint/resume built-in. Nexus GA for cross-namespace composition. Worker auto-tuning GA. OpenAI Agents SDK integration in preview. Python SDK supports 3.10-3.14. Adds durability layer that LangGraph alone lacks for multi-hour pipeline runs. | HIGH |

**Architecture:** LangGraph handles the agent graph (node execution, state transitions, parallel branches). Temporal wraps the overall SDLC pipeline for durability (if the server crashes mid-pipeline, Temporal resumes from the last checkpoint). They are complementary, not competing.

**NOT recommended:** CrewAI (higher-level, less control over graph topology), AutoGen (Microsoft, different paradigm -- conversation-based not graph-based), Semantic Kernel (enterprise-heavy, .NET-first). These are all valid frameworks but don't match CodeBot's graph-centric architecture.

### 4. Multi-LLM Abstraction Layer

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **LiteLLM Proxy** | 1.82+ (stable) | Unified multi-LLM gateway | 39K stars, MIT. Supports 100+ providers in OpenAI-compatible format. 8ms P95 latency at 1K RPS. Already in `docker-compose.yml`. Cost tracking, load balancing, fallback chains, guardrails, rate limiting. v1.82 adds streaming hot-path fixes, Redis pipeline batching. | HIGH |
| **RouteLLM** | latest | Intelligent cost/quality routing | Published at ICLR 2025. 85% cost reduction while maintaining 95% of GPT-4 performance. Transfer learning lets routers generalize to new model pairs. Use as a routing layer on top of LiteLLM. | MEDIUM |
| **Langfuse** | v4 (server) / v4.0+ (Python SDK) | LLM observability, tracing, evals | 23K stars. OpenTelemetry-native since 2025. Already in `docker-compose.yml`. Traces, prompt management, evaluations, cost tracking. V4 (March 2026) moves to observation-centric data model with 10x dashboard speed. | HIGH |

**LLM Provider SDKs (direct, for CLI agent integration):**

| Provider | SDK | Models | Purpose |
|---|---|---|---|
| **Anthropic** | `anthropic` Python SDK + Claude Agent SDK | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 | Primary reasoning, code generation |
| **OpenAI** | `openai` Python SDK | GPT-4.1, o3, o4-mini | Alternative reasoning, embeddings |
| **Google** | `google-genai` Python SDK | Gemini 2.5 Pro, 2.5 Flash | Alternative reasoning, multimodal |

**NOT recommended:** Not-Diamond (proprietary, black-box routing), custom routing from scratch (RouteLLM handles this with trained models).

### 5. MCP (Model Context Protocol)

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **FastMCP** | 3.1+ | MCP server framework for agent tools | Evolved from the official MCP Python SDK. Now at v3.1 with component versioning, granular authorization, OpenTelemetry tracing, session state, dynamic component enable/disable. Streamable HTTP transport is production standard. | HIGH |

**NOT recommended:** Raw `mcp` SDK (FastMCP is the high-level layer on top of it, providing better DX).

### 6. Event Bus & Task Queue

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **NATS + JetStream** | 2.x | Inter-agent messaging, event streaming | Already implemented and tested. Lightweight, high-throughput, JetStream for persistence and replay. Apache-2.0. Running in Docker Compose. | HIGH |
| **Taskiq** | latest | Async task scheduling | ~1.8K stars, MIT. Fully async-native (unlike Celery). NATS broker via `taskiq-nats` JetStreamBroker. FastAPI integration available. Small but active community. | MEDIUM |

**NOT recommended:** Celery (synchronous core, requires Redis/RabbitMQ separately, poor async support), Dramatiq (limited broker options), Kafka (overkill for this scale -- NATS is lighter and faster for agent messaging).

### 7. Database & Storage

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **PostgreSQL** | 16+ | Primary relational store | Projects, runs, tasks, agents, findings, usage logs. Already in Docker Compose. Industry standard. | HIGH |
| **SQLAlchemy** | 2.0+ (async) | ORM / database access | Async support via `asyncio` extension. Already a dependency with `asyncpg`. Type-safe queries, Alembic migrations. | HIGH |
| **Alembic** | 1.14+ | Schema migrations | Already configured and in use. Standard SQLAlchemy migration tool. | HIGH |
| **asyncpg** | 0.30+ | PostgreSQL async driver | Already a dependency. Fastest Python PostgreSQL driver. | HIGH |
| **Redis** | 7+ | Cache, rate limiting, session state | Already in Docker Compose. Used for LiteLLM state, agent state caching, pub/sub fallback. NOT used as primary event bus (that's NATS). | HIGH |

### 8. Vector Store & RAG

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **LanceDB** | 0.29+ | Embedded vector DB (dev/local) | Zero-config, embedded, no server process needed. Built on Lance columnar format (Rust). Supports vector + full-text + SQL search. Billion-scale with millisecond latency. GPU indexing. Arrow-native. Perfect for development and single-server deployments. | HIGH |
| **Qdrant** | 1.17+ | Production vector DB (scaled) | Rust-native, sub-100ms filtered search. GPU-accelerated HNSW indexing (2025). Relevance feedback (2026). Available as managed cloud or self-hosted. Use when horizontal scaling needed beyond single server. | HIGH |
| **LlamaIndex** | 0.14+ | RAG pipeline orchestration | 47.7K stars, MIT. Document chunking, retrieval, re-ranking. 300+ integration packages. Agentic RAG capabilities. Provides the ingestion and retrieval pipeline that feeds context to agents. | HIGH |

**NOT recommended:** ChromaDB (deprecated in architecture docs in favor of LanceDB for embedded use), Pinecone (proprietary), Weaviate (heavier operational burden than LanceDB/Qdrant).

### 9. Knowledge & Memory

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **Cognee** | 0.5+ | Knowledge graph engine | 14K stars, Apache-2.0. Combines vector search + graph databases + cognitive science. Multi-tenant, multilingual, LlamaIndex/LangChain integration. Supports structured outputs. Knowledge graphs for architecture decisions and dependency relationships. | MEDIUM |
| **Letta** (MemGPT) | 0.16+ | Agent memory hierarchy | 15K stars, Apache-2.0. MemGPT pattern: LLM-as-OS with self-editing memory. Core/archival/recall memory tiers. Model-agnostic. Conversations API for shared agent memory. Good fit for episodic memory and cross-session learning. | MEDIUM |

**Confidence note:** Both Cognee and Letta are younger, fast-moving projects. The core concepts (knowledge graphs, tiered agent memory) are sound, but APIs may shift between minor versions. Pin versions carefully.

**NOT recommended:** Neo4j directly (Cognee abstracts graph DB choice with kuzu/neo4j/networkx backends), raw embedding storage (LlamaIndex + vector store handles this better).

### 10. Code Parsing & Analysis

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **tree-sitter** | py-tree-sitter 0.25+ | AST-aware code parsing | 24K stars. Pre-compiled wheels for all platforms. Language grammars as separate packages. Incremental parsing. Foundation for context management's code indexing. | HIGH |
| **ast-grep** | 0.42+ (Python + CLI) | Structural code search and rewrite | Rust-native, fast. Pattern-based AST matching. MCP server available for AI integration. Complements tree-sitter for search/lint/rewrite operations. | HIGH |

### 11. Frontend (Dashboard)

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **React** | 18+ | UI framework | Largest ecosystem, most LLM tooling integration. Server Components support. | HIGH |
| **Vite** | 6+ | Build tool | Fast HMR, ESM-native. First-class Tailwind v4 plugin. Standard for React in 2026. | HIGH |
| **Tailwind CSS** | 4.0+ | Styling | Ground-up rewrite with Rust-powered Oxide engine. CSS-first config, 5x faster builds. Automatic content detection. Container queries built-in. OKLCH colors. | HIGH |
| **shadcn/ui** | latest (CLI v4) | Component library | Copy-paste ownership model. Built on Radix UI + Tailwind. RTL support, dark mode, SSR. React Flow workflow editor template. Unified `radix-ui` package. Massive ecosystem. | HIGH |
| **@xyflow/react** (React Flow) | 12.10+ | Agent graph visualization | The standard node-based UI library. SSR support, dark mode, shadcn/ui component integration. Workflow editor template available. | HIGH |
| **Zustand** | 5.0+ | Client state management | 4M weekly downloads. Minimal API, no Provider needed. Standard pairing with TanStack Query. | HIGH |
| **TanStack Query** | 5.90+ (React) | Server state / data fetching | Standard for React data fetching. Suspense integration. Background refetch, optimistic updates. Complements Zustand (server vs client state). | HIGH |
| **Monaco Editor** | latest | In-browser code editor | VS Code's editor. Standard for code viewing/editing in dashboards. | HIGH |
| **xterm.js** | latest | Terminal emulator | Standard web terminal. Used for agent output streaming. | HIGH |
| **Socket.IO** | 4.8+ (server) / 5.16+ (Python) | Real-time communication | Event-based WebSocket with fallback. Namespaces and rooms for agent channels. Already planned in architecture. | HIGH |
| **Yjs** | 13.6+ | CRDT collaborative editing | 900K weekly downloads. Used by Proton Docs, Evernote, ClickUp. Formally verified. Monaco + Yjs integration available. | HIGH |

**NOT recommended:** MUI (heavy bundle, Tailwind + shadcn/ui covers this), Redux (Zustand + TanStack Query is the 2026 standard), Next.js (SSR not needed for a dashboard app -- Vite SPA is simpler and faster).

### 12. CLI Application

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **Click** | 8.x | Python CLI framework | Composable, decorator-based. Well-documented. Standard Python CLI choice alongside Typer. Architecture docs specify Click. | HIGH |

**Alternative considered:** Typer (built on Click, adds type hints). Either is fine; Click has broader documentation and the architecture already specifies it.

### 13. Security & Quality Pipeline

| Category | Tool | Version | Integration | Confidence |
|---|---|---|---|---|
| **SAST** | Semgrep | latest | CLI subprocess, rule packs | HIGH |
| **SAST + Quality** | SonarQube Community | latest | REST API, quality profiles | HIGH |
| **SAST (GitHub)** | CodeQL | latest | GitHub Actions | HIGH |
| **DAST** | OWASP ZAP | latest | CLI subprocess, API scanning | HIGH |
| **Python Security** | Bandit | latest | CLI subprocess, AST linter | HIGH |
| **Container Scanning** | Trivy | latest | CLI subprocess | HIGH |
| **SBOM + Vuln** | Syft + Grype | latest | SBOM generation + vuln matching | HIGH |
| **Secrets Detection** | Gitleaks | latest | CLI subprocess + pre-commit | HIGH |
| **License Compliance** | ORT | latest | CLI subprocess, dependency analysis | MEDIUM |
| **IaC Security** | KICS | latest | CLI subprocess | MEDIUM |
| **Linting (Python)** | Ruff | 0.7+ | Already configured. Format + lint. Replaces black + isort + flake8. | HIGH |
| **Type Checking** | mypy | 1.13+ (strict) | Already configured. `--strict` mode. | HIGH |

### 14. Observability & Monitoring

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **Langfuse** | v4 | LLM-specific observability | Tracing, prompt management, evals, cost tracking. Already in Docker Compose. OpenTelemetry-native. | HIGH |
| **OpenTelemetry** | latest | Distributed tracing standard | Langfuse, Dagger, FastMCP all emit OTEL traces. Standard across the stack. | HIGH |

### 15. Infrastructure & CI/CD

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **Docker** | latest | Containerization | Standard. Already in use via Docker Compose. | HIGH |
| **Docker Compose** | 3.9+ | Local development stack | Already configured with PostgreSQL, Redis, NATS, Langfuse, LiteLLM. | HIGH |
| **Kubernetes** | latest | Production orchestration | Standard for production container orchestration. | HIGH |
| **Pulumi** | 5.0+ | Infrastructure as Code (programmatic) | Write IaC in Python/TypeScript -- matches CodeBot's stack. Testable with pytest/Jest. 150+ cloud providers. Can consume Terraform modules directly. | MEDIUM |
| **OpenTofu** | 1.0+ | IaC (Terraform-compatible) | Open-source Terraform fork under Linux Foundation. MPL 2.0. Drop-in Terraform replacement. State encryption by default. Use when existing Terraform modules are available. | MEDIUM |
| **Dagger** | 0.20+ | CI/CD pipeline engine | By Docker's co-founder. Write CI/CD in Python/TypeScript. Runs identically local and in CI. Container-sandboxed. Full OTEL tracing. Daggerverse module ecosystem. | MEDIUM |
| **Turborepo** | 2.3+ | Monorepo build orchestration | Already configured. Fast builds, caching, task graph. Good Python/Node hybrid support. | HIGH |

**NOT recommended:** Terraform (BSL-licensed since 2023, use OpenTofu instead), Jenkins (legacy), GitHub Actions alone (Dagger provides local reproducibility).

### 16. Package Management & Tooling

| Technology | Version | Purpose | Why | Confidence |
|---|---|---|---|---|
| **uv** | latest | Python package manager | Already configured. 10-100x faster than pip. Workspace support. Lock files. | HIGH |
| **pnpm** | 9.14+ | Node package manager | Already configured. Efficient disk usage via hard links. Workspace support. | HIGH |
| **Turborepo** | 2.3+ | Monorepo task orchestration | Already configured. Cached builds, parallel execution. | HIGH |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|---|---|---|---|
| Graph Engine | LangGraph | CrewAI, AutoGen | CrewAI too high-level; AutoGen is conversation-based not graph-based |
| Workflow | Temporal | Prefect, Dagster | Prefect/Dagster are data pipeline tools, not agent workflow engines |
| LLM Gateway | LiteLLM | Custom proxy, Portkey | LiteLLM is MIT, 100+ providers, proven at scale |
| Vector Store (dev) | LanceDB | ChromaDB | ChromaDB deprecated in architecture; LanceDB is faster, embedded, Arrow-native |
| Vector Store (prod) | Qdrant | Milvus, Weaviate | Qdrant is Rust-native, simpler ops, better filtering; Milvus heavier |
| RAG Pipeline | LlamaIndex | LangChain retrieval | LlamaIndex is purpose-built for RAG; LangChain is broader but shallower on retrieval |
| State Management | Zustand | Redux, Jotai | Redux is overkill for dashboard; Jotai is atom-based -- store-based Zustand is simpler |
| CSS | Tailwind 4 | CSS Modules, styled-components | Tailwind + shadcn/ui is the 2026 standard; CSS-in-JS is declining |
| IaC | Pulumi + OpenTofu | Terraform | Terraform is BSL-licensed; Pulumi offers Python/TS IaC; OpenTofu is open-source Terraform |
| Task Queue | Taskiq | Celery | Celery has poor async support; Taskiq is async-native with NATS broker |
| CI/CD | Dagger | GitHub Actions alone | Dagger runs identically local and CI; Actions are CI-only |
| Knowledge Graph | Cognee | Neo4j direct | Cognee abstracts graph DB choice, adds AI-native features |
| Agent Memory | Letta | Custom implementation | Letta implements the MemGPT pattern with formal memory tiers; building from scratch is months of work |
| MCP Framework | FastMCP 3.x | Raw MCP SDK | FastMCP is the high-level framework; raw SDK is lower-level boilerplate |
| Routing | RouteLLM | Not-Diamond | RouteLLM is open-source with published research; Not-Diamond is proprietary |

---

## Installation

### Python Core (Backend)

```bash
# Core framework
uv add fastapi[standard] uvicorn[standard] pydantic pydantic-settings

# Database
uv add "sqlalchemy[asyncio]" asyncpg alembic

# Event bus & task queue
uv add nats-py taskiq taskiq-nats

# Cache
uv add "redis[hiredis]"

# Agent graph engine
uv add langgraph temporalio

# LLM gateway (Python SDK)
uv add litellm

# LLM provider SDKs
uv add anthropic openai google-genai

# MCP
uv add fastmcp

# RAG & vector
uv add llama-index lancedb

# Knowledge & memory
uv add cognee letta-client

# Code parsing
uv add tree-sitter ast-grep-py

# Observability
uv add langfuse opentelemetry-sdk opentelemetry-api

# CI/CD
uv add dagger-io
```

### Python Dev Dependencies

```bash
uv add --dev pytest pytest-asyncio httpx ruff mypy
```

### Node (Dashboard)

```bash
# Core
pnpm -F dashboard add react react-dom @xyflow/react zustand @tanstack/react-query

# UI
pnpm -F dashboard add tailwindcss @tailwindcss/vite

# Components (shadcn/ui -- via CLI)
npx shadcn@latest init

# Real-time
pnpm -F dashboard add socket.io-client yjs y-websocket

# Editor & terminal
pnpm -F dashboard add monaco-editor xterm @xterm/addon-fit

# Dev
pnpm -F dashboard add -D vite @vitejs/plugin-react typescript vitest @testing-library/react
```

### Docker Services (already configured)

```bash
docker compose up -d  # PostgreSQL, Redis, NATS, Langfuse, LiteLLM
```

---

## Version Pinning Strategy

| Category | Strategy | Rationale |
|---|---|---|
| **Core framework** (FastAPI, LangGraph, Temporal) | Pin major + minor, allow patch | Stability-critical; patch updates for security fixes |
| **LLM SDKs** (anthropic, openai, google-genai) | Pin minor, allow patch | APIs change frequently; need to track new model releases |
| **UI libraries** (React, Tailwind, shadcn/ui) | Pin major, allow minor + patch | Well-maintained semver; minor updates add features safely |
| **Security tools** (Semgrep, Trivy, Gitleaks) | Latest | Always want newest detection rules |
| **Young/fast-moving** (Cognee, Letta, RouteLLM) | Pin exact version | APIs may break between minors; test before upgrading |

---

## Sources

### Context7 / Official Documentation
- [LangGraph 1.0 Announcement](https://blog.langchain.com/langchain-langgraph-1dot0/) -- HIGH confidence
- [Temporal Python SDK on PyPI](https://pypi.org/project/temporalio/) -- HIGH confidence
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) -- HIGH confidence
- [Tailwind CSS v4](https://tailwindcss.com/blog/tailwindcss-v4) -- HIGH confidence

### Official Releases / GitHub
- [LiteLLM v1.82.0 Release Notes](https://docs.litellm.ai/release_notes/v1-82-0) -- HIGH confidence
- [LiteLLM on GitHub](https://github.com/BerriAI/litellm) -- HIGH confidence
- [FastMCP on PyPI](https://pypi.org/project/fastmcp/) -- HIGH confidence
- [LanceDB on GitHub](https://github.com/lancedb/lancedb) -- HIGH confidence
- [Qdrant 2025 Recap](https://qdrant.tech/blog/2025-recap/) -- HIGH confidence
- [LlamaIndex on PyPI](https://pypi.org/project/llama-index/) -- HIGH confidence
- [Cognee on GitHub](https://github.com/topoteretes/cognee) -- HIGH confidence
- [Letta on GitHub](https://github.com/letta-ai/letta) -- HIGH confidence
- [Langfuse V4 Simplification](https://langfuse.com/blog/2026-03-10-simplify-langfuse-for-scale) -- HIGH confidence
- [React Flow (@xyflow/react) on npm](https://www.npmjs.com/package/@xyflow/react) -- HIGH confidence
- [Zustand on npm](https://www.npmjs.com/package/zustand) -- HIGH confidence
- [TanStack Query on npm](https://www.npmjs.com/package/@tanstack/react-query) -- HIGH confidence
- [Yjs on GitHub](https://github.com/yjs/yjs) -- HIGH confidence
- [Socket.IO on npm](https://www.npmjs.com/package/socket.io) -- HIGH confidence
- [Dagger on GitHub](https://github.com/dagger/dagger) -- MEDIUM confidence
- [Taskiq on GitHub](https://github.com/taskiq-python/taskiq) -- MEDIUM confidence
- [tree-sitter Python bindings](https://pypi.org/project/tree-sitter/) -- HIGH confidence
- [ast-grep on PyPI](https://pypi.org/project/ast-grep-py/) -- HIGH confidence
- [RouteLLM on GitHub](https://github.com/lm-sys/RouteLLM) -- MEDIUM confidence
- [shadcn/ui Changelog](https://ui.shadcn.com/docs/changelog) -- HIGH confidence

### Web Search (verified with multiple sources)
- [Temporal Nexus GA and 2025 Announcements](https://temporal.io/blog/replay-2025-product-announcements) -- MEDIUM confidence
- [Pulumi vs OpenTofu 2026](https://dasroot.net/posts/2026/01/infrastructure-as-code-terraform-opentofu-pulumi-comparison-2026/) -- MEDIUM confidence
- [React State Management 2026](https://www.pkgpulse.com/blog/state-of-react-state-management-2026) -- MEDIUM confidence
