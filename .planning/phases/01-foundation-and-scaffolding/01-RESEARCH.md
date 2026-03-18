# Phase 1: Foundation and Scaffolding - Research

**Researched:** 2026-03-18
**Domain:** Monorepo scaffolding, Docker Compose infrastructure, database schema migrations, shared type definitions, event bus
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire foundation that every subsequent phase builds upon: a Turborepo monorepo with Python and TypeScript workspaces, a Docker Compose dev stack (PostgreSQL, Redis, NATS, LanceDB), database schemas via SQLAlchemy 2.0 async + Alembic, shared Pydantic/TypeScript type definitions, and a working NATS JetStream event bus.

All five requirements (REQ-001 through REQ-005) use well-established, extensively documented technologies. The primary complexity is not in any single technology but in getting them to work together correctly in a polyglot monorepo: Turborepo orchestrating both pnpm workspaces (TypeScript) and uv-managed Python packages, async SQLAlchemy with asyncpg requiring the correct Alembic async template, and NATS JetStream requiring stream/consumer configuration before messages flow. There are also several discrepancies in the existing `pyproject.toml` and `package.json` files that must be corrected during scaffolding.

**Primary recommendation:** Build the monorepo skeleton first (REQ-001), then Docker Compose services (REQ-002), then database schemas (REQ-003), then shared types (REQ-004), then event bus (REQ-005) -- each depends on the previous being functional.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-001 | Turborepo monorepo with apps/ (server, dashboard, cli) and libs/ (agent-sdk, shared-types, graph-engine) | Turborepo + pnpm workspaces pattern; Python packages need package.json shims with uv-delegated scripts; turbo.json task pipeline configuration |
| REQ-002 | Docker Compose dev stack (PostgreSQL, Redis, NATS, LanceDB/Qdrant) | Standard docker-compose.yml with named volumes, healthchecks, and environment variables; NATS needs JetStream enabled via --js flag |
| REQ-003 | Database schemas (SQLAlchemy models, Alembic migrations) for pipeline state, agent tasks, LLM usage | SQLAlchemy 2.0 async with asyncpg; Alembic initialized with `-t async` template; 13+ tables from DATA_MODELS.md |
| REQ-004 | Shared type definitions (Python Pydantic models, TypeScript shared-types lib) | Pydantic v2 models as source of truth; pydantic-to-typescript or JSON Schema export for TS type generation; libs/shared-types as npm package |
| REQ-005 | Event bus (NATS JetStream) for async agent messaging and dashboard streaming | nats-py with JetStream context; streams must be created before publish; push and pull subscriber patterns |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Turborepo | ^2.3.0 | Monorepo build orchestration | Cached task execution across apps/ and libs/; language-agnostic task runner |
| pnpm | 9.14.0 | Node.js package manager | Strict dependency isolation prevents phantom deps; workspace protocol for monorepo |
| uv | latest | Python package and environment manager | 10-100x faster than pip; standard pyproject.toml; workspace support for Python packages |
| Docker Compose | v2 | Local dev infrastructure | Declarative multi-service orchestration; healthchecks for dependency ordering |
| PostgreSQL | 16 | Primary relational database | Pipeline state, agent tasks, checkpoints, LLM usage; asyncpg for async access |
| Redis | 7 | Cache, rate limiting, ephemeral state | redis[hiredis] for C extension performance |
| NATS | latest (with JetStream) | Event bus for agent messaging | Sub-millisecond pub/sub; JetStream adds persistence and at-least-once delivery |
| LanceDB | >=0.13.0 | Embedded vector store (dev) | Apache Arrow native; no separate server process needed in dev |
| SQLAlchemy | >=2.0.35 | ORM with async support | 2.0 async API with MappedColumn; Pydantic-level type safety |
| Alembic | >=1.14.0 | Database migrations | Autogenerate from SQLAlchemy model diffs; async template for asyncpg |
| asyncpg | >=0.30.0 | Async PostgreSQL driver | Required by SQLAlchemy 2.0 async; do NOT use psycopg2 |
| Pydantic | >=2.9.0 | Data validation, shared types | Rust-backed validation; JSON Schema export for TS type generation |
| nats-py | >=2.9.0 | Python NATS client with JetStream | Async-native; JetStream context for durable messaging |
| TypeScript | >=5.5.0 | Type-safe frontend and SDK code | Strict mode with project-specific compiler options |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | >=2.5.0 | Environment-based config | Loading database URLs, NATS URLs, Redis URLs from .env files |
| aiosqlite | >=0.20.0 | Async SQLite driver | Optional: for running tests without PostgreSQL |
| pytest | >=8.3.0 | Python test framework | Validating migrations, event bus connectivity |
| pytest-asyncio | >=0.24.0 | Async test support | Testing NATS JetStream pub/sub, async SQLAlchemy queries |
| ruff | >=0.7.0 | Python linter and formatter | Pre-commit formatting and linting |
| mypy | >=1.13.0 | Python type checker (strict) | Validating Pydantic models and SQLAlchemy types |
| Biome | latest | TS/JS linter and formatter | Replaces ESLint + Prettier for TypeScript packages |
| pydantic-to-typescript | >=2.0.0 | Generate TS types from Pydantic models | Keeping shared-types lib in sync with Python models |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Turborepo | Nx | Nx has better native polyglot support but steeper learning curve; Turborepo is simpler and already in package.json |
| pydantic-to-typescript | JSON Schema + json-schema-to-typescript | More manual but avoids a dependency; pydantic-to-typescript wraps this anyway |
| LanceDB | Qdrant (dev) | Qdrant needs a separate server process; LanceDB embeds directly -- simpler for dev |
| asyncpg | psycopg3 (async) | psycopg3 also supports async but asyncpg has better benchmarks and is the SQLAlchemy async recommendation |

**Installation (Python):**
```bash
uv sync  # installs from pyproject.toml
```

**Installation (Node.js):**
```bash
pnpm install  # installs all workspace dependencies
```

## Architecture Patterns

### Recommended Project Structure (Phase 1 Scope)
```
codebot/
├── apps/
│   ├── server/                    # FastAPI backend (Python)
│   │   ├── pyproject.toml         # Server-specific Python deps
│   │   ├── package.json           # Turborepo shim (scripts delegate to uv)
│   │   ├── src/
│   │   │   └── codebot/
│   │   │       ├── __init__.py
│   │   │       ├── main.py        # FastAPI app entrypoint (minimal for Phase 1)
│   │   │       ├── config.py      # pydantic-settings based config
│   │   │       ├── db/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── engine.py  # async engine + session factory
│   │   │       │   └── models/    # SQLAlchemy ORM models
│   │   │       │       ├── __init__.py
│   │   │       │       ├── base.py        # DeclarativeBase
│   │   │       │       ├── project.py     # Project, Pipeline, PipelinePhase
│   │   │       │       ├── agent.py       # Agent, AgentExecution
│   │   │       │       ├── task.py        # Task
│   │   │       │       ├── artifact.py    # CodeArtifact
│   │   │       │       ├── test_result.py # TestResult
│   │   │       │       ├── security.py    # SecurityFinding
│   │   │       │       ├── review.py      # ReviewComment
│   │   │       │       ├── event.py       # Event
│   │   │       │       ├── checkpoint.py  # Checkpoint
│   │   │       │       ├── experiment.py  # ExperimentLog
│   │   │       │       └── user.py        # User, ApiKey, AuditLog
│   │   │       └── events/
│   │   │           ├── __init__.py
│   │   │           └── bus.py     # NATS JetStream wrapper
│   │   ├── migrations/            # Alembic migrations directory
│   │   │   ├── env.py             # Async migration environment
│   │   │   ├── script.py.mako     # Migration template
│   │   │   └── versions/          # Generated migration files
│   │   ├── alembic.ini            # Alembic config
│   │   └── tests/
│   │       ├── conftest.py        # Async fixtures, DB setup
│   │       ├── test_db.py         # Migration and query tests
│   │       └── test_events.py     # NATS JetStream pub/sub test
│   ├── dashboard/                 # React dashboard (skeleton only)
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   └── src/
│   │       └── main.tsx           # Minimal entrypoint
│   └── cli/                       # TypeScript CLI (skeleton only)
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           └── index.ts           # Minimal entrypoint
├── libs/
│   ├── agent-sdk/                 # Python agent base classes (stub)
│   │   ├── pyproject.toml
│   │   ├── package.json           # Turborepo shim
│   │   └── src/
│   │       └── agent_sdk/
│   │           └── __init__.py
│   ├── shared-types/              # TypeScript shared types
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── index.ts           # Barrel export
│   │       ├── project.ts         # Project, Pipeline types
│   │       ├── agent.ts           # Agent, AgentExecution types
│   │       ├── task.ts            # Task types
│   │       ├── events.ts          # Event types (mirrors NATS subjects)
│   │       └── enums.ts           # All status/type enums
│   └── graph-engine/              # Python graph engine (stub)
│       ├── pyproject.toml
│       ├── package.json           # Turborepo shim
│       └── src/
│           └── graph_engine/
│               └── __init__.py
├── configs/                       # YAML configs (empty structure for now)
│   ├── pipelines/
│   ├── agents/
│   └── providers/
├── docker-compose.yml             # PostgreSQL, Redis, NATS, LanceDB
├── .env.example                   # Environment variable template
├── Makefile                       # make dev, make test, make migrate, etc.
├── pyproject.toml                 # Python workspace root (uv)
├── package.json                   # Node.js workspace root (pnpm)
├── pnpm-workspace.yaml            # pnpm workspace declaration
├── turbo.json                     # Turborepo task pipeline
├── .gitignore
└── .pre-commit-config.yaml        # ruff, mypy, gitleaks hooks
```

### Pattern 1: Turborepo with Python Package Shims

**What:** Turborepo discovers workspaces via pnpm's `package.json` convention. Python packages need a `package.json` shim that delegates scripts to `uv run`.

**When to use:** Any mixed Python/TypeScript monorepo using Turborepo.

**Example:**
```json
// apps/server/package.json (shim for Turborepo)
{
  "name": "@codebot/server",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "build": "echo 'Python build handled by uv'",
    "test": "uv run pytest",
    "lint": "uv run ruff check src/",
    "typecheck": "uv run mypy src/",
    "migrate": "uv run alembic upgrade head",
    "dev": "uv run uvicorn codebot.main:app --reload --host 0.0.0.0 --port 8000"
  }
}
```

### Pattern 2: SQLAlchemy 2.0 Async with DeclarativeBase

**What:** SQLAlchemy 2.0 introduces `MappedAsBase` with typed column declarations. Use `async_sessionmaker` for async operations.

**When to use:** All database access in CodeBot.

**Example:**
```python
# apps/server/src/codebot/db/models/base.py
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# apps/server/src/codebot/db/engine.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from codebot.config import settings

engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://...
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### Pattern 3: Alembic Async Migration Setup

**What:** Initialize Alembic with the async template to use asyncpg. Migration scripts themselves remain synchronous (this is by design -- Alembic handles the async/sync bridge internally).

**When to use:** Database schema migrations with async engines.

**Example:**
```bash
# Initialize Alembic with async template
cd apps/server
uv run alembic init -t async migrations
```

```python
# migrations/env.py (key modifications)
from codebot.db.models.base import Base
from codebot.config import settings

# Set target metadata for autogeneration
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(url=url, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
```

### Pattern 4: NATS JetStream Pub/Sub

**What:** NATS JetStream requires creating streams before publishing. Use `nc.jetstream()` to get a JetStream context. Streams are configured with subjects they accept.

**When to use:** All inter-agent messaging and dashboard event streaming.

**Example:**
```python
# apps/server/src/codebot/events/bus.py
import nats
from nats.js.api import StreamConfig

async def create_event_bus(nats_url: str = "nats://localhost:4222"):
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    # Create the main event stream (idempotent)
    await js.add_stream(
        StreamConfig(
            name="codebot-events",
            subjects=["codebot.events.>"],  # wildcard for all event types
            retention="limits",
            max_msgs=100_000,
        )
    )
    return nc, js

async def publish_event(js, event_type: str, payload: bytes) -> None:
    subject = f"codebot.events.{event_type}"
    ack = await js.publish(subject, payload)
    return ack

async def subscribe_events(js, event_type: str = ">"):
    subject = f"codebot.events.{event_type}"
    sub = await js.subscribe(subject, durable="dashboard")
    return sub
```

### Anti-Patterns to Avoid

- **Hardcoding database URLs in alembic.ini:** Use `config.set_main_option()` in `env.py` to read from environment variables or pydantic-settings.
- **Using psycopg2 with async SQLAlchemy:** Must use asyncpg. psycopg2 will block the event loop.
- **Publishing to NATS without creating streams first:** JetStream requires stream configuration before any messages can be published; `js.publish()` to a subject with no matching stream raises `NoStreamResponse`.
- **Hoisting all dependencies to root package.json:** Each workspace should declare its own dependencies. Root package.json should only have devDependencies for tooling (turbo, typescript).
- **Using `pip install` instead of `uv sync`:** Breaks reproducibility. Always use `uv sync` to install from lockfile.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migrations | Custom SQL scripts or manual DDL | Alembic with autogenerate | Handles upgrade/downgrade, revision chaining, merge heads |
| Type sync (Python to TS) | Manual duplicate type definitions | pydantic-to-typescript or JSON Schema export | Models will drift; automated generation catches it |
| Dev infrastructure orchestration | Shell scripts to start services | Docker Compose with healthchecks | Deterministic startup order, volume management, port mapping |
| Environment config | os.getenv() scattered in code | pydantic-settings BaseSettings | Validation, type coercion, .env file support, nested config |
| Async DB sessions | Manual connection management | SQLAlchemy async_sessionmaker | Connection pooling, transaction management, proper cleanup |

**Key insight:** Phase 1 is pure infrastructure -- every component has a mature, well-tested solution. Building custom alternatives here creates maintenance burden with zero business value.

## Common Pitfalls

### Pitfall 1: Existing Config Discrepancies
**What goes wrong:** The current `pyproject.toml` and `package.json` have several inconsistencies with the design docs that will cause problems if not corrected.
**Why it happens:** Initial files were created before design decisions were finalized.
**Specific issues:**
- `pyproject.toml` targets `python_version = "3.11"` in mypy and `target-version = "py311"` in ruff, but the design docs specify Python 3.12+
- `pyproject.toml` has `requires-python = ">=3.11"` but should be `>=3.12`
- `package.json` includes `next` (Next.js) but the design uses Vite, not Next.js
- `package.json` includes `yjs` and `y-monaco` (CRDT), which are deferred to v2+
- `package.json` includes `@tremor/react` but design uses Shadcn/ui + Recharts
- `package.json` includes `eslint` but design uses Biome
- `package.json` declares `react: ^19.0.0` but design docs say `>=18.3.0`
- `package.json` uses `workspaces` (npm/yarn convention) but project uses pnpm (needs `pnpm-workspace.yaml`)
- Root `package.json` has dashboard dependencies hoisted to root level -- they should be in `apps/dashboard/package.json`
**How to avoid:** Create clean configs from scratch based on design docs, not modifying existing files.

### Pitfall 2: Alembic Async Template Selection
**What goes wrong:** Running `alembic init migrations` (without `-t async`) generates a synchronous `env.py` that uses `create_engine()`, which is incompatible with asyncpg.
**Why it happens:** Default Alembic template is synchronous.
**How to avoid:** Always use `alembic init -t async migrations` when using asyncpg.
**Warning signs:** `sqlalchemy.exc.ArgumentError` about async driver, or `RuntimeError: cannot use await outside async function`.

### Pitfall 3: NATS JetStream Stream Pre-Creation
**What goes wrong:** Publishing to a NATS subject without a matching JetStream stream raises `NoStreamResponse` or silently drops the message.
**Why it happens:** JetStream streams must be explicitly created with subject patterns before they accept messages.
**How to avoid:** Create streams in application startup (FastAPI lifespan) or in a dedicated init script. Use `add_stream()` which is idempotent.
**Warning signs:** Published messages never arrive at subscribers; `nats.js.errors.NotFoundError`.

### Pitfall 4: Docker Compose Service Startup Order
**What goes wrong:** The FastAPI server starts before PostgreSQL or NATS are ready, causing connection failures.
**Why it happens:** `depends_on` only waits for container start, not service readiness.
**How to avoid:** Use `depends_on` with `condition: service_healthy` and define healthchecks for PostgreSQL (`pg_isready`), Redis (`redis-cli ping`), and NATS (TCP check on port 4222).
**Warning signs:** Intermittent connection errors on first `docker-compose up`.

### Pitfall 5: SQLAlchemy Model Import Order for Alembic Autogeneration
**What goes wrong:** Alembic autogenerate produces empty migrations because models are not imported before `target_metadata` is set.
**Why it happens:** SQLAlchemy's DeclarativeBase only registers models when their modules are imported.
**How to avoid:** Ensure `migrations/env.py` imports all model modules (or uses a models `__init__.py` that does barrel imports) before referencing `Base.metadata`.
**Warning signs:** `alembic revision --autogenerate` creates a migration with empty `upgrade()` and `downgrade()`.

### Pitfall 6: pnpm-workspace.yaml Required for pnpm Workspaces
**What goes wrong:** `pnpm install` does not recognize workspaces if `pnpm-workspace.yaml` is missing.
**Why it happens:** pnpm requires an explicit `pnpm-workspace.yaml` file (unlike npm which reads `workspaces` from `package.json`).
**How to avoid:** Create `pnpm-workspace.yaml` at repo root listing all workspace paths.
**Warning signs:** `pnpm install` installs everything in root `node_modules` without workspace linking.

## Code Examples

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: codebot
      POSTGRES_PASSWORD: codebot_dev
      POSTGRES_DB: codebot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codebot"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  nats:
    image: nats:latest
    command: ["--js", "--sd", "/data"]  # Enable JetStream with storage
    ports:
      - "4222:4222"   # Client connections
      - "8222:8222"   # HTTP monitoring
    volumes:
      - nats_data:/data
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8222/healthz"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  nats_data:
```

### pnpm-workspace.yaml
```yaml
packages:
  - "apps/*"
  - "libs/*"
  - "sdks/*"
```

### turbo.json
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "cache": false
    },
    "lint": {},
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "migrate": {
      "cache": false
    }
  }
}
```

### Pydantic Settings Configuration
```python
# apps/server/src/codebot/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://codebot:codebot_dev@localhost:5432/codebot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # NATS
    nats_url: str = "nats://localhost:4222"

    # Application
    debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_prefix": "CODEBOT_"}

settings = Settings()
```

### NATS JetStream Test Pattern
```python
# apps/server/tests/test_events.py
import asyncio
import pytest
import nats

@pytest.mark.asyncio
async def test_jetstream_pub_sub():
    """Verify NATS JetStream publish and subscribe within 1 second."""
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    # Create stream
    await js.add_stream(name="test-stream", subjects=["test.>"])

    # Subscribe
    sub = await js.subscribe("test.hello")

    # Publish
    await js.publish("test.hello", b"world")

    # Receive within 1 second
    msg = await asyncio.wait_for(sub.next_msg(), timeout=1.0)
    assert msg.data == b"world"
    await msg.ack()

    # Cleanup
    await js.delete_stream("test-stream")
    await nc.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pip + requirements.txt | uv + pyproject.toml | 2024 | 10-100x faster installs; lockfile for reproducibility |
| SQLAlchemy 1.x sync | SQLAlchemy 2.0 async | 2023 | Native async with asyncpg; MappedColumn typing |
| Alembic sync only | Alembic async template | 2023 | `-t async` template generates async env.py |
| ChromaDB | LanceDB (dev) / Qdrant (prod) | 2025 | ChromaDB degrades above ~1M vectors; LanceDB is Arrow-native |
| ESLint + Prettier | Biome | 2024-2025 | Single binary, 35x faster; replaces two tools |
| npm/yarn workspaces | pnpm workspaces | 2023-2024 | Content-addressable store; strict isolation |
| Pydantic v1 | Pydantic v2 | 2023 | Rust-backed validation; 10-50x faster; breaking API |

**Deprecated/outdated in existing project files:**
- `next` in root package.json: Project uses Vite, not Next.js
- `eslint` in root package.json: Replace with Biome
- `yjs`, `y-monaco`: Deferred to v2+
- `@tremor/react`: Design uses Shadcn/ui + Recharts

## Open Questions

1. **uv workspaces vs separate pyproject.toml per Python package**
   - What we know: uv supports workspaces via `[tool.uv.workspace]` in the root pyproject.toml. Each Python package (server, agent-sdk, graph-engine) can be a workspace member.
   - What's unclear: Whether uv workspace mode works smoothly with Turborepo's task discovery, or if separate `uv sync` per package is needed.
   - Recommendation: Use uv workspaces at the root pyproject.toml level. Each Python package has its own pyproject.toml with dependencies. Turborepo shim package.json scripts delegate to `uv run` in each package directory.

2. **LanceDB inclusion in Docker Compose**
   - What we know: LanceDB is embedded (runs in-process, no server). It stores data on the local filesystem.
   - What's unclear: Whether it should be in Docker Compose at all -- it has no server component.
   - Recommendation: Do NOT add LanceDB to Docker Compose. It runs embedded. Just ensure a data directory exists. The REQ-002 docker-compose should include PostgreSQL, Redis, and NATS only.

3. **Shared Pydantic models location**
   - What we know: The design has `libs/agent-sdk/` (Python) and `libs/shared-types/` (TypeScript) as separate packages.
   - What's unclear: Where the canonical Pydantic models live -- in `libs/agent-sdk/` or in `apps/server/`? The database models must be in the server, but the API/event schemas should be shared.
   - Recommendation: Database ORM models live in `apps/server/src/codebot/db/models/`. Shared Pydantic schemas (for API contracts, event payloads) live in `libs/agent-sdk/` and are imported by the server. TypeScript types in `libs/shared-types/` are generated from these Pydantic models.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.3.0 with pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` (exists) |
| Quick run command | `uv run pytest tests/ -x --timeout=30` |
| Full suite command | `uv run pytest tests/ -v --cov=codebot` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-001 | `turbo build` completes for all workspaces | smoke | `pnpm turbo build` | No -- Wave 0 |
| REQ-001 | `uv sync` and `pnpm install` succeed from clean clone | smoke | `uv sync && pnpm install` | No -- Wave 0 |
| REQ-002 | Docker Compose brings up all services healthy | integration | `docker-compose up -d && docker-compose ps` | No -- Wave 0 |
| REQ-003 | Alembic migrations apply cleanly | integration | `uv run alembic upgrade head` | No -- Wave 0 |
| REQ-003 | All tables created correctly | unit | `uv run pytest tests/test_db.py -x` | No -- Wave 0 |
| REQ-004 | Pydantic models compile and are importable | unit | `uv run python -c "from agent_sdk import ..."` | No -- Wave 0 |
| REQ-004 | TypeScript types compile | smoke | `pnpm --filter @codebot/shared-types build` | No -- Wave 0 |
| REQ-005 | NATS JetStream pub/sub within 1 second | integration | `uv run pytest tests/test_events.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x --timeout=30` (quick Python tests)
- **Per wave merge:** `pnpm turbo build && uv run pytest tests/ -v`
- **Phase gate:** Full suite green + `docker-compose up` smoke test before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `apps/server/tests/conftest.py` -- async fixtures, database setup/teardown
- [ ] `apps/server/tests/test_db.py` -- covers REQ-003 (migration apply, table creation, basic CRUD)
- [ ] `apps/server/tests/test_events.py` -- covers REQ-005 (NATS JetStream pub/sub roundtrip)
- [ ] Framework already configured in pyproject.toml (`asyncio_mode = "auto"`, `testpaths = ["tests"]`)

## Sources

### Primary (HIGH confidence)
- Project docs: `docs/design/DATA_MODELS.md` v2.5 -- all 13+ table schemas for SQLAlchemy models
- Project docs: `docs/design/PROJECT_STRUCTURE.md` v2.5 -- complete directory layout
- Project docs: `docs/technical/TECHNICAL_REQUIREMENTS.md` v2.5 -- version pins, compiler options
- `.planning/research/STACK.md` -- full stack decisions with rationale
- `.planning/research/ARCHITECTURE.md` -- build order tiers, component boundaries
- Existing `pyproject.toml` and `package.json` -- current state (with discrepancies noted)

### Secondary (MEDIUM confidence)
- [Turborepo docs: Structuring a repository](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository) -- workspace patterns
- [Turborepo discussion #1077](https://github.com/vercel/turborepo/discussions/1077) -- Python packages in Turborepo via package.json shims
- [pnpm workspaces docs](https://pnpm.io/workspaces) -- pnpm-workspace.yaml required
- [nats-py GitHub](https://github.com/nats-io/nats.py) -- JetStream API, stream configuration
- [NATS JetStream docs](https://docs.nats.io/nats-concepts/jetstream) -- stream/consumer concepts
- [Alembic async cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) -- async template, env.py patterns
- [FastAPI + async SQLAlchemy + Alembic guide](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) -- end-to-end setup pattern
- [pydantic-to-typescript v2.0.0](https://github.com/phillipdupuis/pydantic-to-typescript) -- Pydantic v2 support confirmed

### Tertiary (LOW confidence)
- [uv workspace support discussion](https://github.com/astral-sh/uv/issues/6935) -- uv monorepo patterns still evolving
- [Monorepo Tools 2026 comparison](https://viadreams.cc/en/blog/monorepo-tools-2026/) -- Turborepo vs Nx vs alternatives

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all technologies are mature, well-documented, and already specified in project research
- Architecture: HIGH -- directory structure and patterns directly from project design docs
- Pitfalls: HIGH -- discrepancies verified by reading actual project files; async patterns verified via official docs
- Event bus: HIGH -- nats-py JetStream API verified via official GitHub repo and docs

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable technologies, 30-day validity)
