# Technology Stack

**Project:** CodeBot -- Autonomous Multi-Agent SDLC Platform
**Researched:** 2026-03-18
**Updated:** 2026-03-18 (license audit for open-source compliance)
**Overall Confidence:** HIGH

---

## Open-Source Licensing Policy

**User preference: MIT / Apache-2.0 licensed stack.** Every recommendation below has been audited for license compatibility. Dependencies are categorized as:

- **CLEAN** -- MIT, Apache-2.0, BSD-2/3, PostgreSQL License, ISC. Fully permissive.
- **CAUTION** -- LGPL-2.1/3.0, MPL-2.0. Open source but with copyleft conditions on modifications to the library itself (not your application code when dynamically linked). Acceptable for use, but modifications to the library must remain open.
- **FLAG** -- Mixed licensing (open core with commercial extensions), restrictive rule licenses, or source-available components. Documented with mitigation.

See [License Audit](#license-audit) section for the full breakdown.

---

## Recommended Stack

This document prescribes the full technology stack for CodeBot. Choices are informed by the existing monorepo foundation (Turborepo, uv, pnpm, Docker Compose with PostgreSQL/Redis/NATS already running), the architecture documents (v2.5), and current ecosystem research as of March 2026.

---

### 1. Core Languages & Runtime

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **Python** | 3.12+ | PSF-2.0 (CLEAN) | Backend, orchestration, agents, graph engine | Dominant language for AI/ML tooling. LangGraph, Temporal, LiteLLM, LlamaIndex all Python-first. Strict mypy + ruff provides safety. 3.12 has TaskGroup, ExceptionGroup. | HIGH |
| **TypeScript** | 5.5+ | Apache-2.0 (CLEAN) | Dashboard, CLI, shared types | Strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`. ESM only. Industry standard for React + Vite. | HIGH |
| **Node.js** | 22 LTS | MIT (CLEAN) | Runtime for dashboard/CLI | Current LTS. Required by Vite, React, Turborepo. | HIGH |
| **Rust** (indirect) | -- | MIT/Apache-2.0 (CLEAN) | Via tree-sitter, ast-grep, LanceDB, Qdrant | Not written directly, but several critical dependencies are Rust-native, giving us C-level performance for parsing and search. | HIGH |

### 2. Web Framework (Backend)

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **FastAPI** | 0.135+ | MIT (CLEAN) | REST API, WebSocket, SSE | 96K GitHub stars. Async-native, Pydantic v2 integration, automatic OpenAPI docs. Already in `pyproject.toml`. Mature and stable -- the standard Python API framework. | HIGH |
| **Uvicorn** | 0.30+ | BSD-3 (CLEAN) | ASGI server | Standard FastAPI server. Already a dependency. | HIGH |
| **Pydantic** | 2.9+ | MIT (CLEAN) | Validation, serialization, settings | Core to FastAPI. v2 is 5-50x faster than v1. Already in use for shared models in `libs/agent-sdk/`. | HIGH |
| **Pydantic Settings** | 2.5+ | MIT (CLEAN) | Configuration management | 12-factor config from env vars. Already a dependency. | HIGH |

**NOT recommended:** Django/Flask (synchronous-first, heavier ORM coupling), Litestar (smaller ecosystem, less LLM tooling integration).

### 3. Agent Graph Engine

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **LangGraph** | 1.0+ (stable) | MIT (CLEAN) | Stateful agent graph execution | Hit v1.0 in October 2025 with stability commitment. 24.6K stars. Native directed graph execution, durable state persistence, human-in-the-loop, checkpoint/resume, node-level caching (May 2025), dynamic tool calling (Aug 2025), MCP streamable HTTP transport. Used by Uber, LinkedIn, Klarna. `create_agent` is now the standard API. Dropped Python 3.9 support. | HIGH |
| **Temporal** | Python SDK 1.4+ | MIT (CLEAN) | Durable workflow orchestration | 18.9K stars. Retry/checkpoint/resume built-in. Nexus GA for cross-namespace composition. Worker auto-tuning GA. OpenAI Agents SDK integration in preview. Python SDK supports 3.10-3.14. Adds durability layer that LangGraph alone lacks for multi-hour pipeline runs. | HIGH |

**Architecture:** LangGraph handles the agent graph (node execution, state transitions, parallel branches). Temporal wraps the overall SDLC pipeline for durability (if the server crashes mid-pipeline, Temporal resumes from the last checkpoint). They are complementary, not competing.

**NOT recommended:** CrewAI (higher-level, less control over graph topology), AutoGen (Microsoft, different paradigm -- conversation-based not graph-based), Semantic Kernel (enterprise-heavy, .NET-first). These are all valid frameworks but don't match CodeBot's graph-centric architecture.

### 4. Multi-LLM Abstraction Layer

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **LiteLLM Proxy** | 1.82+ (stable) | MIT (CLEAN -- see note) | Unified multi-LLM gateway | 39K stars. Supports 100+ providers in OpenAI-compatible format. 8ms P95 latency at 1K RPS. Already in `docker-compose.yml`. Cost tracking, load balancing, fallback chains, guardrails, rate limiting. v1.82 adds streaming hot-path fixes, Redis pipeline batching. | HIGH |
| **RouteLLM** | latest | Apache-2.0 (CLEAN) | Intelligent cost/quality routing | Published at ICLR 2025. 85% cost reduction while maintaining 95% of GPT-4 performance. Transfer learning lets routers generalize to new model pairs. Use as a routing layer on top of LiteLLM. | MEDIUM |
| **Langfuse** | v4 (server) / v4.0+ (Python SDK) | MIT (CLEAN -- see note) | LLM observability, tracing, evals | 23K stars. OpenTelemetry-native since 2025. Already in `docker-compose.yml`. Traces, prompt management, evaluations, cost tracking. V4 (March 2026) moves to observation-centric data model with 10x dashboard speed. All product features open-sourced under MIT since June 2025. | HIGH |

> **LiteLLM license note:** Core SDK and proxy are MIT. The `enterprise/` directory contains SSO, RBAC, SCIM features under a separate commercial license. CodeBot does not need these enterprise governance features -- we use LiteLLM as a self-hosted proxy, not a multi-tenant SaaS. **No license concern for our use case.**

> **Langfuse license note:** Core product features are MIT since June 2025 (previously some were commercial-only). Only SCIM, audit logs, and data retention policies remain commercially licensed. CodeBot's use (tracing, evals, prompt management) is fully covered by the MIT-licensed core. **No license concern.**

**LLM Provider SDKs (direct, for CLI agent integration):**

| Provider | SDK | License | Models | Purpose |
|---|---|---|---|---|
| **Anthropic** | `anthropic` Python SDK + Claude Agent SDK | MIT (CLEAN) | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 | Primary reasoning, code generation |
| **OpenAI** | `openai` Python SDK | Apache-2.0 (CLEAN) | GPT-4.1, o3, o4-mini | Alternative reasoning, embeddings |
| **Google** | `google-genai` Python SDK | Apache-2.0 (CLEAN) | Gemini 2.5 Pro, 2.5 Flash | Alternative reasoning, multimodal |

**NOT recommended:** Not-Diamond (proprietary, black-box routing), custom routing from scratch (RouteLLM handles this with trained models).

### 5. MCP (Model Context Protocol)

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **FastMCP** | 3.1+ | Apache-2.0 (CLEAN) | MCP server framework for agent tools | Evolved from the official MCP Python SDK. Now at v3.1 with component versioning, granular authorization, OpenTelemetry tracing, session state, dynamic component enable/disable. Streamable HTTP transport is production standard. | HIGH |

**NOT recommended:** Raw `mcp` SDK (FastMCP is the high-level layer on top of it, providing better DX).

### 6. Event Bus & Task Queue

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **NATS + JetStream** | 2.x | Apache-2.0 (CLEAN) | Inter-agent messaging, event streaming | Already implemented and tested. Lightweight, high-throughput, JetStream for persistence and replay. Running in Docker Compose. | HIGH |
| **Taskiq** | latest | MIT (CLEAN) | Async task scheduling | ~1.8K stars. Fully async-native (unlike Celery). NATS broker via `taskiq-nats` JetStreamBroker. FastAPI integration available. Small but active community. | MEDIUM |

**NOT recommended:** Celery (synchronous core, requires Redis/RabbitMQ separately, poor async support), Dramatiq (limited broker options), Kafka (overkill for this scale -- NATS is lighter and faster for agent messaging).

### 7. Database & Storage

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **PostgreSQL** | 16+ | PostgreSQL License (CLEAN) | Primary relational store | Projects, runs, tasks, agents, findings, usage logs. Already in Docker Compose. Industry standard. | HIGH |
| **SQLAlchemy** | 2.0+ (async) | MIT (CLEAN) | ORM / database access | Async support via `asyncio` extension. Already a dependency with `asyncpg`. Type-safe queries, Alembic migrations. | HIGH |
| **Alembic** | 1.14+ | MIT (CLEAN) | Schema migrations | Already configured and in use. Standard SQLAlchemy migration tool. | HIGH |
| **asyncpg** | 0.30+ | Apache-2.0 (CLEAN) | PostgreSQL async driver | Already a dependency. Fastest Python PostgreSQL driver. | HIGH |
| **Redis** | 7+ | BSD-3 (CLEAN) | Cache, rate limiting, session state | Already in Docker Compose. Used for LiteLLM state, agent state caching, pub/sub fallback. NOT used as primary event bus (that's NATS). | HIGH |

### 8. Vector Store & RAG

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **LanceDB** | 0.29+ | Apache-2.0 (CLEAN) | Embedded vector DB (dev/local) | Zero-config, embedded, no server process needed. Built on Lance columnar format (Rust). Supports vector + full-text + SQL search. Billion-scale with millisecond latency. GPU indexing. Arrow-native. Perfect for development and single-server deployments. | HIGH |
| **Qdrant** | 1.17+ | Apache-2.0 (CLEAN) | Production vector DB (scaled) | Rust-native, sub-100ms filtered search. GPU-accelerated HNSW indexing (2025). Relevance feedback (2026). Available as managed cloud or self-hosted. Use when horizontal scaling needed beyond single server. | HIGH |
| **LlamaIndex** | 0.14+ | MIT (CLEAN) | RAG pipeline orchestration | 47.7K stars. Document chunking, retrieval, re-ranking. 300+ integration packages. Agentic RAG capabilities. Provides the ingestion and retrieval pipeline that feeds context to agents. | HIGH |

**NOT recommended:** ChromaDB (deprecated in architecture docs in favor of LanceDB for embedded use), Pinecone (proprietary), Weaviate (heavier operational burden than LanceDB/Qdrant).

### 9. Knowledge & Memory

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **Cognee** | 0.5+ | Apache-2.0 (CLEAN) | Knowledge graph engine | 14K stars. Combines vector search + graph databases + cognitive science. Multi-tenant, multilingual, LlamaIndex/LangChain integration. Supports structured outputs. Knowledge graphs for architecture decisions and dependency relationships. | MEDIUM |
| **Letta** (MemGPT) | 0.16+ | Apache-2.0 (CLEAN) | Agent memory hierarchy | 15K stars. MemGPT pattern: LLM-as-OS with self-editing memory. Core/archival/recall memory tiers. Model-agnostic. Conversations API for shared agent memory. Good fit for episodic memory and cross-session learning. | MEDIUM |

**Confidence note:** Both Cognee and Letta are younger, fast-moving projects. The core concepts (knowledge graphs, tiered agent memory) are sound, but APIs may shift between minor versions. Pin versions carefully.

**NOT recommended:** Neo4j directly (Cognee abstracts graph DB choice with kuzu/neo4j/networkx backends), raw embedding storage (LlamaIndex + vector store handles this better).

### 10. Code Parsing & Analysis

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **tree-sitter** | py-tree-sitter 0.25+ | MIT (CLEAN) | AST-aware code parsing | 24K stars. Pre-compiled wheels for all platforms. Language grammars as separate packages. Incremental parsing. Foundation for context management's code indexing. | HIGH |
| **ast-grep** | 0.42+ (Python + CLI) | MIT (CLEAN) | Structural code search and rewrite | Rust-native, fast. Pattern-based AST matching. MCP server available for AI integration. Complements tree-sitter for search/lint/rewrite operations. | HIGH |

### 11. Frontend (Dashboard)

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **React** | 18+ | MIT (CLEAN) | UI framework | Largest ecosystem, most LLM tooling integration. Server Components support. | HIGH |
| **Vite** | 6+ | MIT (CLEAN) | Build tool | Fast HMR, ESM-native. First-class Tailwind v4 plugin. Standard for React in 2026. | HIGH |
| **Tailwind CSS** | 4.0+ | MIT (CLEAN) | Styling | Ground-up rewrite with Rust-powered Oxide engine. CSS-first config, 5x faster builds. Automatic content detection. Container queries built-in. OKLCH colors. | HIGH |
| **shadcn/ui** | latest (CLI v4) | MIT (CLEAN) | Component library | Copy-paste ownership model. Built on Radix UI + Tailwind. RTL support, dark mode, SSR. React Flow workflow editor template. Unified `radix-ui` package. Massive ecosystem. | HIGH |
| **@xyflow/react** (React Flow) | 12.10+ | MIT (CLEAN) | Agent graph visualization | The standard node-based UI library. SSR support, dark mode, shadcn/ui component integration. Workflow editor template available. | HIGH |
| **Zustand** | 5.0+ | MIT (CLEAN) | Client state management | 4M weekly downloads. Minimal API, no Provider needed. Standard pairing with TanStack Query. | HIGH |
| **TanStack Query** | 5.90+ (React) | MIT (CLEAN) | Server state / data fetching | Standard for React data fetching. Suspense integration. Background refetch, optimistic updates. Complements Zustand (server vs client state). | HIGH |
| **Monaco Editor** | latest | MIT (CLEAN) | In-browser code editor | VS Code's editor engine. Standard for code viewing/editing in dashboards. | HIGH |
| **xterm.js** | latest | MIT (CLEAN) | Terminal emulator | Standard web terminal. Used for agent output streaming. | HIGH |
| **Socket.IO** | 4.8+ (server) / 5.16+ (Python) | MIT (CLEAN) | Real-time communication | Event-based WebSocket with fallback. Namespaces and rooms for agent channels. Already planned in architecture. | HIGH |
| **Yjs** | 13.6+ | MIT (CLEAN) | CRDT collaborative editing | 900K weekly downloads. Used by Proton Docs, Evernote, ClickUp. Formally verified. Monaco + Yjs integration available. | HIGH |

**NOT recommended:** MUI (heavy bundle, Tailwind + shadcn/ui covers this), Redux (Zustand + TanStack Query is the 2026 standard), Next.js (SSR not needed for a dashboard app -- Vite SPA is simpler and faster).

### 12. CLI Application

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **Click** | 8.x | BSD-3 (CLEAN) | Python CLI framework | Composable, decorator-based. Well-documented. Standard Python CLI choice alongside Typer. Architecture docs specify Click. | HIGH |

**Alternative considered:** Typer (built on Click, adds type hints, MIT). Either is fine; Click has broader documentation and the architecture already specifies it.

### 13. Security & Quality Pipeline

| Category | Tool | License | Integration | Confidence |
|---|---|---|---|---|
| **SAST** | Semgrep CE engine | LGPL-2.1 (CAUTION) | CLI subprocess | HIGH |
| **SAST** | **Opengrep** (recommended over Semgrep rules) | LGPL-2.1 (CAUTION) | CLI subprocess, open rule sets | HIGH |
| **SAST + Quality** | SonarQube Community Build | LGPL-3.0 core (CAUTION -- see FLAG) | REST API, quality profiles | MEDIUM |
| **DAST** | OWASP ZAP | Apache-2.0 (CLEAN) | CLI subprocess, API scanning | HIGH |
| **Python Security** | Bandit | Apache-2.0 (CLEAN) | CLI subprocess, AST linter | HIGH |
| **Container Scanning** | Trivy | Apache-2.0 (CLEAN) | CLI subprocess | HIGH |
| **SBOM + Vuln** | Syft + Grype | Apache-2.0 (CLEAN) | SBOM generation + vuln matching | HIGH |
| **Secrets Detection** | Gitleaks | MIT (CLEAN) | CLI subprocess + pre-commit | HIGH |
| **License Compliance** | ORT | Apache-2.0 (CLEAN) | CLI subprocess, dependency analysis | MEDIUM |
| **IaC Security** | KICS | Apache-2.0 (CLEAN) | CLI subprocess | MEDIUM |
| **Linting (Python)** | Ruff | MIT (CLEAN) | Already configured. Format + lint. Replaces black + isort + flake8. | HIGH |
| **Type Checking** | mypy | MIT (CLEAN) | Already configured. `--strict` mode. | HIGH |

> **FLAG: Semgrep rules license change.** Semgrep's engine remains LGPL-2.1, but Semgrep-maintained rules moved to the restrictive "Semgrep Rules License v1.0" in late 2024. This license prohibits redistribution and SaaS use. **Mitigation:** Use **Opengrep** (LGPL-2.1 fork, 2.1K stars, backed by 10+ security companies including JIT and Orca Security) which restores taint analysis, inter-procedural scanning, fingerprinting, and uses community-maintained open rule sets. Keep Semgrep CE engine for custom rules you write yourself.

> **FLAG: SonarQube analyzer license change.** SonarQube Community Build's core remains LGPL-3.0, but bundled analyzers moved to "Sonar Source-Available License v1" (SSALv1) since November 2024. This is NOT an OSI-approved open-source license. **Mitigation:** Acceptable for internal use (self-hosted, non-competing). If strict open-source purity is required, use Semgrep/Opengrep + Ruff + Bandit as alternatives for static analysis, which together cover most of SonarQube's value. SonarQube's main advantage is its quality dashboard -- which can be replicated with custom reporting.

> **NOTE: CodeQL removed from core recommendations.** CodeQL requires GitHub Advanced Security license for private repositories (proprietary). Retained only as an optional GitHub Actions integration for public-facing repos, not a core dependency. Semgrep/Opengrep covers the same SAST ground with open licensing.

### 14. Observability & Monitoring

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **Langfuse** | v4 | MIT (CLEAN) | LLM-specific observability | Tracing, prompt management, evals, cost tracking. Already in Docker Compose. OpenTelemetry-native. All product features MIT since June 2025. | HIGH |
| **OpenTelemetry** | latest | Apache-2.0 (CLEAN) | Distributed tracing standard | Langfuse, Dagger, FastMCP all emit OTEL traces. Standard across the stack. | HIGH |

### 15. Infrastructure & CI/CD

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **Docker** | latest | Apache-2.0 (CLEAN) | Containerization | Standard. Already in use via Docker Compose. | HIGH |
| **Docker Compose** | 3.9+ | Apache-2.0 (CLEAN) | Local development stack | Already configured with PostgreSQL, Redis, NATS, Langfuse, LiteLLM. | HIGH |
| **Kubernetes** | latest | Apache-2.0 (CLEAN) | Production orchestration | Standard for production container orchestration. | HIGH |
| **Pulumi** | 5.0+ | Apache-2.0 (CLEAN) | Infrastructure as Code (programmatic) | Write IaC in Python/TypeScript -- matches CodeBot's stack. Testable with pytest/Jest. 150+ cloud providers. Can consume Terraform modules directly. Explicitly committed to Apache-2.0, never BSL. | MEDIUM |
| **OpenTofu** | 1.0+ | MPL-2.0 (CAUTION) | IaC (Terraform-compatible) | Open-source Terraform fork under Linux Foundation. Drop-in Terraform replacement. State encryption by default. MPL-2.0 requires modifications to OpenTofu itself to remain MPL, but using it to provision infra carries no copyleft obligation on your code. | MEDIUM |
| **Dagger** | 0.20+ | Apache-2.0 (CLEAN) | CI/CD pipeline engine | By Docker's co-founder. Write CI/CD in Python/TypeScript. Runs identically local and in CI. Container-sandboxed. Full OTEL tracing. Daggerverse module ecosystem. | MEDIUM |
| **Turborepo** | 2.3+ | MIT (CLEAN) | Monorepo build orchestration | Already configured. Fast builds, caching, task graph. Good Python/Node hybrid support. | HIGH |

**NOT recommended:** Terraform (BSL-licensed since 2023 -- NOT open source, use OpenTofu instead), Jenkins (legacy), GitHub Actions alone (Dagger provides local reproducibility).

### 16. Package Management & Tooling

| Technology | Version | License | Purpose | Why | Confidence |
|---|---|---|---|---|---|
| **uv** | latest | MIT + Apache-2.0 dual (CLEAN) | Python package manager | Already configured. 10-100x faster than pip. Workspace support. Lock files. | HIGH |
| **pnpm** | 9.14+ | MIT (CLEAN) | Node package manager | Already configured. Efficient disk usage via hard links. Workspace support. | HIGH |
| **Turborepo** | 2.3+ | MIT (CLEAN) | Monorepo task orchestration | Already configured. Cached builds, parallel execution. | HIGH |

---

## License Audit

### Summary

| Status | Count | Details |
|---|---|---|
| **CLEAN** (MIT, Apache-2.0, BSD, PSF, ISC, PostgreSQL License) | 48 | All core stack components |
| **CAUTION** (LGPL-2.1, LGPL-3.0, MPL-2.0) | 3 | Semgrep CE engine, SonarQube core, OpenTofu |
| **FLAG** (mixed / source-available components) | 3 | Semgrep rules, SonarQube analyzers, CodeQL |
| **Mitigated** | 2 | LiteLLM enterprise dir, Langfuse enterprise features |

### Full License Table

| Technology | License | Status | Notes |
|---|---|---|---|
| Python | PSF-2.0 | CLEAN | |
| TypeScript | Apache-2.0 | CLEAN | |
| Node.js | MIT | CLEAN | |
| FastAPI | MIT | CLEAN | |
| Uvicorn | BSD-3 | CLEAN | |
| Pydantic / Pydantic Settings | MIT | CLEAN | |
| LangGraph | MIT | CLEAN | |
| Temporal | MIT | CLEAN | |
| LiteLLM (core SDK + proxy) | MIT | CLEAN | enterprise/ directory is commercially licensed; not needed |
| LiteLLM (enterprise/) | Commercial | N/A | Not used by CodeBot |
| RouteLLM | Apache-2.0 | CLEAN | |
| Langfuse (core) | MIT | CLEAN | Since June 2025, all product features MIT |
| Langfuse (SCIM/audit/retention) | Commercial | N/A | Not used by CodeBot |
| FastMCP | Apache-2.0 | CLEAN | |
| NATS | Apache-2.0 | CLEAN | |
| Taskiq | MIT | CLEAN | |
| PostgreSQL | PostgreSQL License | CLEAN | Permissive, similar to BSD/MIT |
| SQLAlchemy | MIT | CLEAN | |
| Alembic | MIT | CLEAN | |
| asyncpg | Apache-2.0 | CLEAN | |
| Redis | BSD-3 | CLEAN | |
| LanceDB | Apache-2.0 | CLEAN | |
| Qdrant | Apache-2.0 | CLEAN | |
| LlamaIndex | MIT | CLEAN | |
| Cognee | Apache-2.0 | CLEAN | |
| Letta (MemGPT) | Apache-2.0 | CLEAN | |
| tree-sitter | MIT | CLEAN | |
| ast-grep | MIT | CLEAN | |
| React | MIT | CLEAN | |
| Vite | MIT | CLEAN | |
| Tailwind CSS | MIT | CLEAN | |
| shadcn/ui | MIT | CLEAN | |
| @xyflow/react (React Flow) | MIT | CLEAN | |
| Zustand | MIT | CLEAN | |
| TanStack Query | MIT | CLEAN | |
| Monaco Editor | MIT | CLEAN | |
| xterm.js | MIT | CLEAN | |
| Socket.IO | MIT | CLEAN | |
| Yjs | MIT | CLEAN | |
| Click | BSD-3 | CLEAN | |
| **Semgrep CE engine** | **LGPL-2.1** | **CAUTION** | Engine is LGPL. Rules moved to restrictive license. Use Opengrep for rules. |
| **Opengrep** | **LGPL-2.1** | **CAUTION** | Community fork restoring open features + rules |
| **SonarQube Community Build (core)** | **LGPL-3.0** | **CAUTION** | Core is LGPL-3. Bundled analyzers are SSALv1 (source-available, not OSI). |
| OWASP ZAP | Apache-2.0 | CLEAN | |
| Bandit | Apache-2.0 | CLEAN | |
| Trivy | Apache-2.0 | CLEAN | |
| Syft | Apache-2.0 | CLEAN | |
| Grype | Apache-2.0 | CLEAN | |
| Gitleaks | MIT | CLEAN | |
| ORT | Apache-2.0 | CLEAN | |
| KICS | Apache-2.0 | CLEAN | |
| Ruff | MIT | CLEAN | |
| mypy | MIT | CLEAN | |
| OpenTelemetry | Apache-2.0 | CLEAN | |
| Docker | Apache-2.0 | CLEAN | |
| Kubernetes | Apache-2.0 | CLEAN | |
| Pulumi | Apache-2.0 | CLEAN | |
| **OpenTofu** | **MPL-2.0** | **CAUTION** | Modifications to OpenTofu itself must stay MPL. Using it to provision infra is fine. |
| Dagger | Apache-2.0 | CLEAN | |
| Turborepo | MIT | CLEAN | |
| uv | MIT + Apache-2.0 dual | CLEAN | |
| pnpm | MIT | CLEAN | |
| Anthropic SDK | MIT | CLEAN | |
| OpenAI SDK | Apache-2.0 | CLEAN | |
| Google GenAI SDK | Apache-2.0 | CLEAN | |

### Recommendations for Flagged Items

1. **Semgrep rules**: Use Opengrep fork + community rule sets. Write custom rules under your own license. Do NOT redistribute Semgrep's proprietary rules.
2. **SonarQube analyzers**: Accept SSALv1 for internal use (self-hosted, non-competing). If strict OSS purity required, replace with Semgrep/Opengrep + Ruff + Bandit.
3. **CodeQL**: Use only for public repos via GitHub Actions. Not a core dependency. Semgrep/Opengrep covers SAST for private repos.
4. **LiteLLM enterprise features**: Not needed. Core proxy is MIT.
5. **Langfuse enterprise features**: Not needed. Core product is MIT since June 2025.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|---|---|---|---|
| Graph Engine | LangGraph (MIT) | CrewAI, AutoGen | CrewAI too high-level; AutoGen is conversation-based not graph-based |
| Workflow | Temporal (MIT) | Prefect, Dagster | Prefect/Dagster are data pipeline tools, not agent workflow engines |
| LLM Gateway | LiteLLM (MIT) | Custom proxy, Portkey | LiteLLM is MIT, 100+ providers, proven at scale. Portkey is proprietary. |
| Vector Store (dev) | LanceDB (Apache-2.0) | ChromaDB | ChromaDB deprecated in architecture; LanceDB is faster, embedded, Arrow-native |
| Vector Store (prod) | Qdrant (Apache-2.0) | Milvus, Weaviate | Qdrant is Rust-native, simpler ops, better filtering; Milvus heavier. All Apache-2.0. |
| RAG Pipeline | LlamaIndex (MIT) | LangChain retrieval | LlamaIndex is purpose-built for RAG; LangChain is broader but shallower on retrieval |
| State Management | Zustand (MIT) | Redux, Jotai | Redux is overkill for dashboard; Jotai is atom-based -- store-based Zustand is simpler |
| CSS | Tailwind 4 (MIT) | CSS Modules, styled-components | Tailwind + shadcn/ui is the 2026 standard; CSS-in-JS is declining |
| IaC | Pulumi (Apache-2.0) + OpenTofu (MPL-2.0) | Terraform (BSL) | **Terraform is BSL-licensed -- NOT open source.** Pulumi is Apache-2.0. OpenTofu is the open fork. |
| Task Queue | Taskiq (MIT) | Celery | Celery has poor async support; Taskiq is async-native with NATS broker |
| CI/CD | Dagger (Apache-2.0) | GitHub Actions alone | Dagger runs identically local and CI; Actions are CI-only |
| Knowledge Graph | Cognee (Apache-2.0) | Neo4j direct | Cognee abstracts graph DB choice, adds AI-native features. Neo4j Community is GPL. |
| Agent Memory | Letta (Apache-2.0) | Custom implementation | Letta implements the MemGPT pattern with formal memory tiers; building from scratch is months of work |
| MCP Framework | FastMCP 3.x (Apache-2.0) | Raw MCP SDK | FastMCP is the high-level framework; raw SDK is lower-level boilerplate |
| Routing | RouteLLM (Apache-2.0) | Not-Diamond | RouteLLM is open-source with published research; **Not-Diamond is proprietary** |
| SAST | Opengrep (LGPL-2.1) | Semgrep rules (proprietary) | **Semgrep rules are no longer openly licensed.** Opengrep restores open rule sets. |

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
| **Security tools** (Opengrep, Trivy, Gitleaks) | Latest | Always want newest detection rules |
| **Young/fast-moving** (Cognee, Letta, RouteLLM) | Pin exact version | APIs may break between minors; test before upgrading |

---

## Sources

### Context7 / Official Documentation
- [LangGraph 1.0 Announcement](https://blog.langchain.com/langchain-langgraph-1dot0/) -- HIGH confidence
- [Temporal Python SDK on PyPI](https://pypi.org/project/temporalio/) -- HIGH confidence
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) -- HIGH confidence
- [Tailwind CSS v4](https://tailwindcss.com/blog/tailwindcss-v4) -- HIGH confidence

### Official Releases / GitHub
- [LiteLLM on GitHub (MIT License)](https://github.com/BerriAI/litellm) -- HIGH confidence
- [LiteLLM v1.82.0 Release Notes](https://docs.litellm.ai/release_notes/v1-82-0) -- HIGH confidence
- [LiteLLM License file](https://github.com/BerriAI/litellm/blob/main/LICENSE) -- HIGH confidence
- [Langfuse open-sourcing announcement (June 2025)](https://langfuse.com/blog/2025-06-04-open-sourcing-langfuse-product) -- HIGH confidence
- [Langfuse License (MIT)](https://github.com/langfuse/langfuse/blob/main/LICENSE) -- HIGH confidence
- [FastMCP on PyPI](https://pypi.org/project/fastmcp/) -- HIGH confidence
- [LanceDB on GitHub (Apache-2.0)](https://github.com/lancedb/lancedb) -- HIGH confidence
- [Qdrant on GitHub (Apache-2.0)](https://github.com/qdrant/qdrant) -- HIGH confidence
- [LlamaIndex on PyPI (MIT)](https://pypi.org/project/llama-index/) -- HIGH confidence
- [Cognee on GitHub (Apache-2.0)](https://github.com/topoteretes/cognee) -- HIGH confidence
- [Letta on GitHub (Apache-2.0)](https://github.com/letta-ai/letta) -- HIGH confidence
- [Letta License file](https://github.com/letta-ai/letta-code/blob/main/LICENSE) -- HIGH confidence
- [React Flow / xyflow (MIT)](https://github.com/xyflow/xyflow) -- HIGH confidence
- [xyflow open-source commitment](https://xyflow.com/open-source) -- HIGH confidence
- [Monaco Editor License (MIT)](https://github.com/microsoft/monaco-editor/blob/main/LICENSE.txt) -- HIGH confidence
- [Zustand on npm (MIT)](https://www.npmjs.com/package/zustand) -- HIGH confidence
- [TanStack Query on npm (MIT)](https://www.npmjs.com/package/@tanstack/react-query) -- HIGH confidence
- [Yjs on GitHub (MIT)](https://github.com/yjs/yjs) -- HIGH confidence
- [Socket.IO on npm (MIT)](https://www.npmjs.com/package/socket.io) -- HIGH confidence
- [Dagger License (Apache-2.0)](https://github.com/dagger/dagger/blob/main/LICENSE) -- HIGH confidence
- [Pulumi License (Apache-2.0)](https://github.com/pulumi/pulumi/blob/master/LICENSE) -- HIGH confidence
- [Pulumi open-source commitment](https://www.pulumi.com/blog/pulumi-hearts-opensource/) -- HIGH confidence
- [Turborepo on GitHub (MIT)](https://github.com/vercel/turborepo) -- HIGH confidence
- [Taskiq on GitHub (MIT)](https://github.com/taskiq-python/taskiq) -- MEDIUM confidence
- [RouteLLM on GitHub (Apache-2.0)](https://github.com/lm-sys/RouteLLM) -- MEDIUM confidence
- [shadcn/ui Changelog](https://ui.shadcn.com/docs/changelog) -- HIGH confidence

### License-Specific Sources
- [Semgrep licensing page](https://semgrep.dev/docs/licensing) -- HIGH confidence
- [Opengrep fork (LGPL-2.1)](https://www.infoq.com/news/2025/02/semgrep-forked-opengrep/) -- HIGH confidence
- [SonarQube Community Build license](https://www.sonarsource.com/license/) -- HIGH confidence
- [SonarQube SSALv1 change](https://www.sonarsource.com/open-source-editions/sonarqube-community-edition/) -- HIGH confidence
- [OpenTofu (MPL-2.0 under Linux Foundation)](https://opentofu.org/) -- HIGH confidence
- [Terraform BSL license change](https://www.hashicorp.com/en/blog/hashicorp-adopts-business-source-license) -- HIGH confidence

### Web Search (verified with multiple sources)
- [Temporal Nexus GA and 2025 Announcements](https://temporal.io/blog/replay-2025-product-announcements) -- MEDIUM confidence
- [Pulumi vs OpenTofu 2026](https://dasroot.net/posts/2026/01/infrastructure-as-code-terraform-opentofu-pulumi-comparison-2026/) -- MEDIUM confidence
- [React State Management 2026](https://www.pkgpulse.com/blog/state-of-react-state-management-2026) -- MEDIUM confidence
