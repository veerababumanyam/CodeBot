# Stack Research

**Domain:** Autonomous multi-agent SDLC platform with graph-based orchestration, multi-LLM support, sandboxed execution, and web dashboard
**Researched:** 2026-03-18
**Confidence:** MEDIUM-HIGH (existing project docs at v2.5 are authoritative; web/external verification unavailable in this session; key choices grounded in well-established community projects)

---

## Recommended Stack

### Core Technologies

#### Backend / Orchestration (Python)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Primary runtime for all backend, orchestration, and agent logic | 3.12 introduces the specializing adaptive interpreter (meaningful perf gains for hot agent loops), `type` statement, improved error messages, `asyncio.TaskGroup` + `ExceptionGroup` for structured concurrency — all required by the CodeBot architecture |
| FastAPI | >=0.115.0 | HTTP API layer, WebSocket streaming, OpenAPI generation | Async-first, auto-generates OpenAPI docs (needed for LLM tool-call integrations), native WebSocket support for real-time agent streaming, production-proven at scale |
| Pydantic | >=2.9.0 | Data validation, settings management, LLM output parsing | v2 is Rust-backed (10–50x faster than v1), required by FastAPI and LangGraph; strict mode catches agent message schema violations at runtime |
| Uvicorn | >=0.30.0 | ASGI server for FastAPI | Lowest-latency production ASGI server; `uvicorn[standard]` includes `uvloop` + `httptools` for ~2x throughput over baseline |
| LangGraph | >=0.2.x | Agent graph engine — DAG execution with cycles, fan-out parallelism, checkpointing, human-in-the-loop | Only Python agent framework that natively models cyclical agent graphs (S8 Debug loop requires cycles); built-in Postgres-backed checkpointing avoids reinventing persistence; ~24.6K stars MIT |
| Temporal | >=1.x (Python SDK `temporalio`) | Durable workflow orchestration — automatic retry, scheduling, failure recovery across the 11-stage SDLC pipeline | LangGraph handles graph logic; Temporal handles durability. Long-running pipelines (hours per project) require durable execution that survives process crashes; used in production by Stripe, Netflix, Datadog. ~18.9K stars MIT |
| LiteLLM | >=1.82.0 | Unified LLM gateway for 100+ providers with cost tracking, rate limiting, fallback chains | Single interface replaces per-provider SDKs; built-in token counting + cost attribution feeds CodeBot's cost tracker; self-hosted proxy mode enables shared rate-limit pools across 30 agents. ~39.2K stars MIT |
| NATS + JetStream | latest (`nats-py`) | Event bus for typed inter-agent message passing and durable streaming | Sub-millisecond pub/sub latency; JetStream adds at-least-once delivery and stream replay — needed when agents fan out in parallel (S3–S5); CNCF project with ~19.4K stars Apache-2.0 |
| SQLAlchemy | >=2.0.35 | ORM for PostgreSQL/SQLite with async support | 2.0 async API (`async_sessionmaker`) pairs cleanly with FastAPI lifespan; mapped classes with `MappedColumn` provide Pydantic-level type safety at the ORM layer |
| Alembic | >=1.14.0 | Database schema migrations | Single dependency on SQLAlchemy; autogenerate from model diffs; required when pipeline state tables evolve across releases |

#### Frontend / Dashboard (TypeScript + React)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React | >=18.3.0 | UI component model | Industry standard; concurrent rendering handles the high-frequency agent update stream without blocking the main thread |
| Vite | >=6.0.0 | Build tool and dev server | HMR is sub-100ms in large codebases; native ESM, fast cold starts, first-class TypeScript support — superior DX over Webpack/CRA for a dashboard that will be developed in-repo alongside the backend |
| TypeScript | >=5.5.0 | Type-safe frontend and SDK code | Required; strict mode + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes` + `verbatimModuleSyntax` per project conventions |
| TailwindCSS | >=4.0.0 | Utility-first CSS | v4 drops the config file and uses CSS variables natively; zero-runtime overhead; pairs with Shadcn/ui |
| Shadcn/ui | latest | Accessible UI component library (copy-paste pattern) | Not a dependency — components live in the repo, so there are no version lock-in issues. Built on Radix primitives (accessibility-first). The standard choice for new React apps in 2025/2026 |
| React Flow (`@xyflow/react`) | latest | Interactive DAG visualization for the pipeline graph view | The only React library built specifically for node-graph UIs; ELK.js layout engine handles automatic agent graph layout; ~20K stars MIT |
| Monaco Editor (`@monaco-editor/react`) | latest | In-browser code editor and diff viewer | Powers VS Code; supports 90+ languages with syntax highlighting, LSP integration, and diff view for code review display — no realistic alternative |
| xterm.js (`@xterm/xterm`) | latest | In-browser terminal for streaming agent output | Powers VS Code integrated terminal; hardware-accelerated canvas renderer; addon ecosystem (fit, weblinks, search) |
| Zustand | >=5.0.0 | Client state management | Minimal boilerplate for complex agent state (30 concurrent agents updating simultaneously); avoids Redux's ceremony while being more predictable than React Context for high-frequency updates |
| TanStack Query | >=5.60.0 | Server state, data fetching, cache | Declarative data fetching with stale-while-revalidate; handles polling for agent status without custom useEffect loops |
| Socket.IO client | latest | Real-time WebSocket for agent event streaming | Auto-reconnection, rooms (per-project namespaces), binary support for file streaming; pairs with the FastAPI/Socket.IO server side |
| React Router | >=7.0.0 | Client-side routing | v7 is the merged React Router + Remix API; stable, minimal, fits a SPA dashboard pattern |
| Recharts | >=2.13.0 | Chart library for cost/token metrics | Lightweight, composable, SSR-friendly; sufficient for the metrics views (token cost over time, per-agent cost breakdown) |

#### CLI (TypeScript / Node.js)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Node.js | 22.x LTS | CLI runtime | LTS until April 2027; native ESM, stable `fetch`, `--watch` dev mode; supported by all CI environments |
| pnpm | >=9.x | Node package manager | Symlink-based node_modules avoids hoisting issues in the Turborepo monorepo; 2–4x faster installs than npm; strict by default |
| Turborepo | latest | Monorepo build orchestration | Caches task outputs (build, test, typecheck) across `apps/` and `libs/`; pipeline-aware so `dashboard` only rebuilds when `shared-types` changes; the standard monorepo tool for mixed Python/Node repos in 2025 |
| Bun | >=1.1+ | Optional: CLI runtime for performance-sensitive operations | 3–5x faster than Node for script execution; `bun run` is a drop-in for `node` for most CLI use cases; use if CLI latency becomes a pain point |

#### Data Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PostgreSQL | >=16 | Primary relational database — pipeline state, agent configs, project metadata, user data | Mature, reliable, rich ecosystem (`asyncpg` for async, `pgvector` extension if Qdrant is insufficient); Temporal and LangGraph both support Postgres-backed persistence |
| SQLite (`aiosqlite`) | >=0.20.0 | Development database, embedded context store | Zero-config local dev; LanceDB uses its own storage; `aiosqlite` for async SQLAlchemy |
| Redis (`redis-py`) | >=5.2.0 | Cache, session state, rate limiting | Not the event bus (NATS handles that), but essential for JWT session cache, per-agent rate-limit state, and ephemeral pipeline flags. `redis[hiredis]` for C extension performance |
| LanceDB | >=0.15.0 | Embedded vector database for development and L1/L2 context retrieval | Apache Arrow native; embeds directly into the Python process (no separate server in dev); hybrid search (vector + keyword + SQL filter) in a single query; replaces ChromaDB which has performance issues at scale |
| Qdrant | >=1.12.0 (client) | Production vector database | Dedicated server mode with horizontal scaling; Rust-based (high throughput); supports named vectors (multiple embedding models per collection); ~29.6K stars Apache-2.0 |
| DuckDB | latest | In-process OLAP for L2 context queries, cost analytics | Zero-config; SQL over Parquet/Arrow; 10–100x faster than SQLite for analytical queries; ideal for cost aggregation (token spend per agent per run) |

#### Agent Execution & Sandboxing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Docker SDK for Python | >=7.1.0 | Programmatic container lifecycle management | Sandbox containers per coding agent; supports cgroup resource limits (CPU + memory caps per agent); industry standard |
| E2B Sandbox | latest | Secure cloud sandboxes for generated code execution | Microvm-based isolation stronger than Docker alone; 150ms cold start; pre-built Python/Node/Go environments; use for untrusted code generated by agents when gVisor/Kata is unavailable |
| git worktrees (`GitPython`) | >=3.1.43 | Per-agent git isolation | Each coding agent gets its own worktree from the main project repo; prevents file conflicts during parallel S5 implementation phase; standard pattern validated by Automaker, Superset, and other multi-agent coding platforms |
| Tree-sitter | latest | Multi-language AST parsing for code indexing | 100+ language grammars; incremental re-parsing (only re-parses changed nodes); needed for semantic code chunking before vector embedding |

#### LLM Providers and Routing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `anthropic` SDK | >=0.39.0 | Anthropic/Claude API client | Claude Opus 4 for architecture/planning, Claude Sonnet 4 for code gen, Claude Haiku 3.5 for fast completions; extended thinking for complex reasoning |
| `openai` SDK | >=1.55.0 | OpenAI API client | GPT-4.1 for code gen/review, o3/o4-mini for reasoning-heavy debugging and architecture decisions |
| `google-genai` SDK | >=1.0.0 | Google Gemini API client | Gemini 2.5 Pro for 1M+ token long-context analysis (ideal for whole-codebase review); Gemini 2.5 Flash for fast completions |
| LiteLLM Proxy | >=1.82.0 | Unified LLM gateway (self-hosted) | All 30 agents call a single LiteLLM proxy endpoint; proxy handles routing, fallback chains, rate limiting, and token cost tracking centrally rather than per-agent |
| RouteLLM | latest (Apache-2.0) | Cost-quality model routing | Dynamically routes easy tasks to cheaper models and hard tasks to capable models; ICLR 2025 research-backed; reduces LLM spend by 30–50% on mixed-complexity workloads |
| Ollama | latest | Self-hosted LLM runtime | Privacy-sensitive workloads; offline/air-gapped deployments; supports Llama 3, Mistral, CodeLlama, Qwen, DeepSeek |
| LM Studio | latest | Desktop self-hosted LLM runtime | Developer convenience for local model testing; GUI-based model management |

#### MCP and Tooling

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastMCP 2.0 | latest (Apache-2.0) | MCP server and client framework | Powers ~70% of all MCP servers; REST-to-MCP generation; tool composition; ~21.9K stars; enables agents to call external tools (browser, filesystem, APIs) via the standard MCP protocol |
| Taskiq | latest (MIT) | Async Python task queue with NATS broker | Async-native (no sync worker thread pool); NATS broker backend aligns with the NATS event bus; lightweight alternative to Celery for Python 3.12 async workloads |

#### Observability and LLM Ops

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenTelemetry | latest | Distributed tracing across all agents | Vendor-neutral; instruments FastAPI, SQLAlchemy, httpx automatically; traces span from HTTP request through graph execution through each agent tool call |
| Langfuse | latest (MIT) | LLM observability and cost tracking | Per-agent token tracking with session/trace grouping; prompt versioning; self-hostable; 23.3K stars; integrates with LiteLLM via callback |
| Prometheus + Grafana | latest | Platform metrics and dashboards | Industry standard; scrapes FastAPI metrics (request latency, error rates, agent throughput); Grafana dashboards for platform health |
| SigNoz | latest | All-in-one: traces, metrics, logs, LLM observability | OpenTelemetry-native; single deployment replaces separate Jaeger + Prometheus + Grafana stack for simpler ops; open-source |
| Sentry (self-hosted) | latest | Exception tracking and session replay | Catches unhandled exceptions across all 30 agents; source map support for TypeScript; self-hosted to avoid data exfiltration of generated code |

#### Security Pipeline Tools

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Semgrep | >=1.90.0 | SAST for generated code | Fastest multi-language SAST; custom rule support (write rules for CodeBot-specific anti-patterns); JSON output for programmatic gating |
| Trivy | >=0.57.0 | Container and dependency SCA | Scans Docker images and lockfiles; SBOM generation via Syft integration; CRITICAL/HIGH severity gate |
| Gitleaks | latest | Secret detection in generated code | Pre-commit hooks + CI scanning; prevents LLM-generated code from accidentally hard-coding secrets |
| OWASP ZAP | latest | DAST against running applications | Dynamic testing of the application CodeBot generates; automated scan via ZAP API |
| Bandit | latest | Python-specific SAST | Catches Python security anti-patterns in generated Python code; supplements Semgrep's Python rules |
| ORT + ScanCode | latest | License compliance | Automated dependency license scanning; prevents GPLv3 contamination in MIT-licensed generated outputs |

#### Testing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest | >=8.x | Python unit and integration testing | Fixture system handles complex async agent test setups; rich plugin ecosystem (`pytest-asyncio`, `pytest-cov`, `anyio`) |
| pytest-asyncio | latest | Async test support for Python | Required for testing all async agent code with `asyncio.TaskGroup` |
| Vitest | latest (MIT) | TypeScript/JavaScript unit testing | Vite-native; runs in the same transform pipeline as the dashboard build; browser mode for testing React components without jsdom limitations |
| Playwright | latest (Apache-2.0) | End-to-end browser testing | Cross-browser (Chrome, Firefox, WebKit); generates tests from user interactions; required for testing the CodeBot dashboard itself and for the E2E testing stage of generated apps |
| Testcontainers | latest (MIT) | Docker-backed integration tests | Spin up real PostgreSQL, Redis, NATS in test suites; avoids mocking the data layer |
| k6 | latest (AGPL-3.0) | Load testing | JS-based load test scripts; integrates with Grafana Cloud for result visualization; simulates 15+ concurrent agents during stress testing |
| axe-core | latest (MPL-2.0) | Accessibility testing | Zero false positives; WCAG 2.2 AA coverage; Playwright integration via `@axe-core/playwright` |
| Stryker | latest (Apache-2.0) | Mutation testing for TypeScript | Verifies test suite quality by introducing code mutations; ensures the dashboard tests actually catch regressions |
| Pact | latest (MIT) | Consumer-driven contract testing | Tests the contract between the dashboard (consumer) and the FastAPI backend (provider) without full E2E setup |

#### DevOps and IaC

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `uv` | latest | Python package and environment manager | 10–100x faster than pip; resolver is written in Rust; compatible with `pyproject.toml`; the 2025 standard for Python dependency management |
| Pulumi | latest (Apache-2.0) | Programmatic IaC for CodeBot-generated infrastructure | Python/TypeScript-native (no HCL); CodeBot's IaC agent generates Pulumi programs in the same languages the platform is written in; supports AWS, GCP, Azure, Vercel, Fly.io |
| OpenTofu | latest (MPL-2.0) | HCL-based IaC (Terraform-compatible, open-source) | For users who prefer HCL or have existing Terraform state; generated alongside Pulumi as an alternative output |
| Dagger | latest (Apache-2.0) | CI/CD pipelines as code | Python/TypeScript SDK; generated CI pipelines run the same locally and in CI; no YAML; used for CodeBot's own CI and as the generated CI output |
| Copier | latest | Project template scaffolding | Jinja2-based parameterized templates with update/sync (unlike cookiecutter); CodeBot uses Copier for the template gallery feature |

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | >=0.27.0 | Async HTTP client | All outbound HTTP calls from agents (package registry queries, external API calls); supports HTTP/2 |
| `python-jose[cryptography]` | >=3.3.0 | JWT creation and verification | Auth middleware for FastAPI; RS256 signing |
| `passlib[bcrypt]` | >=1.7.4 | Password hashing | User account passwords; bcrypt with configurable work factor |
| `python-multipart` | >=0.0.9 | Multipart file upload parsing | PRD upload endpoint (images, documents, diagrams as multi-modal input) |
| `websockets` | >=13.0 | WebSocket protocol | Real-time agent output streaming to the dashboard |
| `rich` | >=13.9.0 | Terminal formatting for the CLI | Progress bars, tables, syntax-highlighted output in `codebot` CLI commands |
| `click` | >=8.1.0 | CLI framework | `codebot init`, `codebot plan`, `codebot start`, etc. |
| `typer` | >=0.12.0 | Typer wraps Click with type hints | Used for subcommand groups where Click verbosity becomes unwieldy |
| `pluggy` | latest (MIT) | Plugin hook system | Agent plugins, LLM provider plugins, template plugins; battle-tested via pytest |
| `ast-grep` | latest (MIT) | AST-aware code search and rewrite | Structural search and lint via Tree-sitter; used by agents to locate patterns in generated code |
| `LlamaIndex` | latest (MIT) | RAG framework for code-aware retrieval | 150+ data connectors; query planning over the three-tier context system; pairs with LanceDB/Qdrant |
| `Mermaid` | latest (MIT) | Auto-generated diagrams | Architecture diagrams, ERDs, and flow diagrams generated in the documentation phase |
| `Apprise` | latest | Multi-channel notifications | Slack, Discord, email, push — single library for all human-in-the-loop notifications |
| `Renovate` | latest (AGPL-3.0) | Automated dependency updates | Keeps generated project dependencies current; runs as a post-deployment autonomous agent |
| `Langfuse SDK` | latest | LLM cost callback integration | Drop-in LiteLLM callback; zero extra code per agent |
| `Biome` | latest (MIT) | JS/TS linter and formatter | Replaces ESLint + Prettier in a single Rust binary; 35x faster than ESLint; used in generated TS/JS projects |
| `Husky` | latest (MIT) | Git hooks for Node.js | Pre-commit secret scanning and linting in generated projects |
| `simple-git` | latest (MIT) | TypeScript git operations for CLI | Lightweight git bindings for the CLI layer (worktree management from Node.js side) |
| `Lucide React` | >=0.460.0 | Icon set | Consistent, tree-shakeable SVG icons for the dashboard |
| `ELKjs` | latest (EPL-2.0) | Graph layout engine | Automatic layout of agent DAGs in the React Flow visualization; handles complex subgraph arrangements |

---

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `ruff` | Python linter and formatter | Replaces Black + isort + Flake8 + pyupgrade in one binary; 100x faster than Black; run `ruff format` + `ruff check --fix` pre-commit |
| `mypy --strict` | Python static type checking | Required per project conventions; strict mode including `--disallow-untyped-defs`, `--disallow-any-generics`, `--warn-return-any` |
| `pyright` | Alternative Python type checker | Accepted as `mypy` alternative; faster in LSP mode for editor integration |
| `uv` | Python package + env manager | `uv venv` + `uv pip install` + `uv lock` for deterministic installs; replaces `poetry` and `pip-tools` |
| `pnpm` | Node package manager | Strict mode prevents phantom dependencies; workspace protocol for monorepo |
| `Turborepo` | Monorepo task orchestration | Cache pipeline outputs; remote caching via Vercel for CI speedup |
| `Biome` | TS/JS lint + format | Single tool replacing ESLint + Prettier for the dashboard and CLI |
| `Docker Compose` | Local dev stack orchestration | Brings up PostgreSQL, Redis, NATS, Qdrant, LiteLLM proxy, Temporal, SigNoz together; defined in `docker-compose.yml` at repo root |
| `pre-commit` | Git hook framework | Runs ruff, mypy, gitleaks, Biome before each commit |
| `Makefile` | Developer convenience commands | `make dev`, `make test`, `make lint`, `make migrate`, `make sandbox-up` |

---

## Installation

```bash
# Python environment (using uv)
uv venv .venv && source .venv/bin/activate
uv pip install \
  fastapi uvicorn[standard] pydantic sqlalchemy alembic asyncpg aiosqlite \
  langgraph langchain langsmith temporalio \
  litellm routellm nats-py taskiq taskiq-nats \
  anthropic openai google-genai \
  lancedb qdrant-client redis[hiredis] duckdb \
  docker gitpython tree-sitter \
  httpx python-jose[cryptography] passlib[bcrypt] python-multipart websockets \
  rich click typer pluggy \
  llama-index langfuse \
  semgrep bandit trivy gitleaks \
  pytest pytest-asyncio anyio pytest-cov \
  copier apprise

# Node.js environment (using pnpm)
pnpm install

# Dashboard dependencies
pnpm add react react-dom react-router zustand \
  @tanstack/react-query \
  @refinedev/core \
  @xyflow/react \
  @monaco-editor/react \
  @xterm/xterm \
  socket.io-client \
  recharts lucide-react

pnpm add -D vite typescript tailwindcss \
  @types/react @types/react-dom \
  @biomejs/biome \
  vitest @vitest/coverage-v8 \
  playwright @axe-core/playwright

# Dev tooling
pip install ruff mypy pyright pre-commit
npm install -g turbo
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| LangGraph | CrewAI | CrewAI excels at role-based hierarchical agent teams with minimal boilerplate; use if the project is a simpler "team of agents" without the cyclical Debug loop and complex graph topology CodeBot requires |
| LangGraph | AutoGen (Microsoft) | AutoGen's group-chat model is better for conversational multi-agent patterns; lacks native graph checkpointing for long-running pipelines |
| LangGraph | Prefect / Airflow | Prefect/Airflow are DAG task schedulers, not agent graph engines; no agent state management or LLM-aware tooling |
| Temporal | Celery + Redis | Celery is sufficient for simple task queues but lacks durable execution semantics (no automatic retry with state preservation, no workflow versioning); not appropriate for pipelines that run for hours |
| LiteLLM | OpenRouter | OpenRouter is a hosted service (data leaves your infrastructure); LiteLLM is self-hosted and supports private/on-premise models via Ollama; better for code privacy |
| NATS JetStream | Kafka | Kafka is operationally heavier (requires ZooKeeper or KRaft); overkill for CodeBot's throughput; NATS is simpler to operate and sub-millisecond |
| NATS JetStream | RabbitMQ | RabbitMQ lacks the streaming semantics needed for agent event replay; harder to scale |
| LanceDB | ChromaDB | ChromaDB has known performance degradation above ~1M vectors and lacks native hybrid search; LanceDB is Apache Arrow native with better throughput |
| LanceDB | Pinecone | Pinecone is a hosted service; data exfiltration risk for generated code; self-hosted LanceDB + Qdrant covers all use cases |
| Qdrant (prod) | Weaviate | Both are strong; Qdrant is Rust-based (higher throughput), simpler operational model, better price-performance at self-hosted scale |
| Vite | Next.js | Next.js SSR/RSC complexity is unnecessary for the CodeBot dashboard (all data is real-time via WebSocket, not server-rendered); Vite SPA is simpler and faster to build |
| Shadcn/ui | Material UI | MUI carries a heavy default look that requires significant effort to un-MUI; Shadcn/ui is unstyled-by-default with Tailwind, giving full design control |
| Turborepo | Nx | Nx has a steeper learning curve and more configuration; Turborepo is simpler for this repo's mixed Python/Node structure |
| Pulumi | Terraform (HashiCorp) | HashiCorp switched Terraform to BSL license in 2023; OpenTofu is the open-source fork; Pulumi is preferred for programmatic IaC generation in the same language as the platform |
| pytest | unittest | pytest fixtures, parametrize, and plugins are essential for testing 30 async agents; stdlib unittest is inadequate |
| `uv` | poetry | `uv` is 10–100x faster; poetry's lockfile format is non-standard; uv uses standard `pyproject.toml` |
| Biome | ESLint + Prettier | ESLint + Prettier requires separate configs, separate runs, occasional conflicts; Biome is a single binary with both; 35x faster |
| Dagger | GitHub Actions YAML | YAML pipelines are not testable locally; Dagger pipelines run identically locally and in CI with full Python/TS type safety |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Flask / Django | Flask is synchronous (requires Gunicorn + threading hacks for async); Django ORM is synchronous and not composable with asyncio TaskGroup; neither auto-generates OpenAPI | FastAPI |
| Celery | Synchronous worker model doesn't compose with async agent code; no durable execution semantics; requires separate result backend | Temporal + Taskiq |
| ChromaDB | Performance degrades above ~1M vectors; no native hybrid (vector + keyword) search; actively replaced in existing CodeBot docs | LanceDB (dev) / Qdrant (prod) |
| Pinecone / Weaviate Cloud | Hosted services expose generated code to third parties; not acceptable for privacy-sensitive projects | Self-hosted Qdrant |
| Webpack / Create React App | CRA is unmaintained (archived 2023); Webpack is 5–20x slower than Vite for the dashboard development loop | Vite |
| Redux Toolkit | Excessive boilerplate for dashboard state; 30 concurrent agent updates cause too many action dispatches; useSelector performance issues | Zustand |
| OpenRouter | Hosted LLM proxy — code sent to third-party service; no self-hosted model support | LiteLLM (self-hosted proxy) |
| Poetry | Slow resolver (pure Python); lockfile is non-standard; `uv` is a strict superset with 100x better performance | `uv` |
| Flake8 + Black + isort separately | Three separate tools with separate configs and separate CI steps; `ruff` replaces all three in one pass | `ruff` |
| SQLite in production | Concurrent writes from 30+ agents will serialize; no connection pooling; not appropriate for the agent state database | PostgreSQL + asyncpg |
| LangChain as the graph engine | LangChain is a chain composition library, not a graph engine; use LangGraph (built on LangChain primitives) for agent DAGs | LangGraph |
| Aider / Continue CLI | Deferred to v2 per PROJECT.md; Claude Code + Codex + Gemini CLI cover v1 needs | Claude Code SDK, Codex CLI, Gemini CLI |
| vLLM / LocalAI / TGI | Deferred to v2 per PROJECT.md; Ollama and LM Studio cover self-hosted needs for v1 | Ollama, LM Studio |
| CRDT (Yjs) for v1 | Deferred to v2 per PROJECT.md; agents work in isolated worktrees, no real-time human+agent co-editing needed in v1 | Git worktree isolation |
| Native iOS (Swift) / Android (Kotlin) | Out of scope; React Native covers cross-platform mobile | React Native |
| Flutter | Out of scope per PROJECT.md | React Native |

---

## Stack Patterns by Variant

**Development environment (local, single developer):**
- Use SQLite (`aiosqlite`) instead of PostgreSQL
- Use LanceDB embedded (no Qdrant server)
- Use Redis locally via Docker
- Use NATS locally via Docker
- Skip Temporal: use LangGraph checkpointing only for simpler pipeline durability
- Use Ollama for LLM calls to avoid API costs during development
- Single `docker-compose.yml` brings up: Redis, NATS, LiteLLM proxy, SigNoz

**Production (cloud, multi-user):**
- PostgreSQL 16 (RDS or self-hosted with replication)
- Qdrant cluster (3-node minimum for HA)
- Redis cluster or ElastiCache
- NATS cluster with JetStream replication factor 3
- Temporal cluster (3-node minimum)
- LiteLLM proxy as a dedicated service (not embedded in FastAPI)
- SigNoz or Prometheus + Grafana + Jaeger stack

**Air-gapped / privacy-first deployment:**
- Ollama for all LLM inference (Llama 3, DeepSeek, Qwen)
- All vector/relational/cache databases self-hosted
- LiteLLM proxy configured to route 100% to Ollama endpoints
- No external scanning services (run Semgrep/Trivy/Gitleaks locally)

**Generated application targets:**
- Web: React + Vite + TypeScript + Tailwind + Shadcn/ui (default)
- Backend: FastAPI or Express.js or Go/Gin depending on tech stack config
- Mobile: React Native (Expo or bare workflow)
- CI/CD: Dagger pipelines targeting GitHub Actions, GitLab CI, or CircleCI
- IaC: Pulumi (Python/TS) or OpenTofu (HCL)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Python 3.12.x | SQLAlchemy >=2.0.35, FastAPI >=0.115.0, Pydantic >=2.9.0 | All three tested together; `asyncio.TaskGroup` requires 3.11+, use 3.12 for perf |
| LangGraph >=0.2.x | LangChain >=0.3.0 | LangGraph 0.2+ dropped the pre-0.2 API; require `langchain-core` >=0.3.0 |
| FastAPI >=0.115.0 | Pydantic v2 only | FastAPI 0.115+ dropped Pydantic v1 compatibility; do not mix with pydantic <2.0 |
| SQLAlchemy 2.0 async | asyncpg >=0.30.0, aiosqlite >=0.20.0 | 2.0 async API requires explicit async drivers; do not use psycopg2 |
| Vite >=6.0.0 | React >=18.3.0, TypeScript >=5.5.0 | Vite 6 requires Node >=18; recommend Node 22 LTS |
| TailwindCSS >=4.0.0 | PostCSS >=8.x | Tailwind v4 requires PostCSS 8; no longer requires `tailwind.config.js` |
| React Router >=7.0.0 | React >=18.3.0 | React Router 7 is the merged Remix+RR API; breaking changes from v6 (use the migration guide) |
| Temporalio (Python SDK) | Python >=3.9, Temporal server >=1.24 | Python SDK is async-native; server version must match SDK capabilities |
| LiteLLM >=1.82.0 | anthropic >=0.39.0, openai >=1.55.0, google-genai >=1.0.0 | LiteLLM proxies to these SDKs; keep provider SDKs up-to-date with LiteLLM's tested matrix |
| LanceDB >=0.15.0 | lancedb Python package only | Not compatible with ChromaDB APIs; different embedding function interface |

---

## Sources

- `docs/refernces/RESEARCH_SUMMARY.md` v2.5 (2026-03-18) — comprehensive technology evaluation covering all major components; MEDIUM-HIGH confidence (recent, authored for this project, based on GitHub star counts and license verification)
- `docs/technical/TECHNICAL_REQUIREMENTS.md` v2.5 (2026-03-18) — specific version pins and integration patterns for all core dependencies; HIGH confidence for version numbers cited
- `docs/architecture/ARCHITECTURE.md` v2.5 (2026-03-18) — C4 model, subsystem design, data flow; HIGH confidence for architectural decisions
- `CLAUDE.md` (project conventions) — Python/TypeScript standards, monorepo layout, package manager choices; HIGH confidence (project-authoritative)
- `.planning/PROJECT.md` (2026-03-18) — in-scope vs deferred feature decisions; HIGH confidence (project-authoritative)
- MASFactory paper (arXiv:2603.06007) — graph-centric multi-agent design pattern; HIGH confidence for architectural inspiration
- External verification (Context7, WebFetch, WebSearch) — UNAVAILABLE in this session; version numbers from existing project docs cross-referenced with training data through August 2025

---

*Stack research for: CodeBot — autonomous multi-agent SDLC platform*
*Researched: 2026-03-18*
