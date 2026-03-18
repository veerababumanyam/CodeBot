---
phase: 01-foundation-and-scaffolding
plan: "02"
subsystem: database
tags: [docker, postgresql, redis, nats, lancedb, sqlalchemy, alembic, orm]
dependency_graph:
  requires: ["01-01"]
  provides: ["database-schema", "docker-dev-stack", "async-session-factory"]
  affects: ["02-graph-engine", "03-agent-system", "04-api-layer"]
tech_stack:
  added:
    - "SQLAlchemy 2.0 async ORM (asyncpg driver)"
    - "Alembic async migrations"
    - "pytest-asyncio 1.3.0 (asyncio_mode=auto)"
  patterns:
    - "DeclarativeBase with type_annotation_map for UUID/datetime"
    - "TimestampMixin shared across models"
    - "Function-scoped async engine per test (avoids cross-loop issues)"
    - "SAVEPOINT-based test isolation (no DB teardown needed)"
key_files:
  created:
    - "docker-compose.yml — 3 core services (postgres:16, redis:7, nats:2) + 2 observability"
    - "data/lancedb/.gitkeep — embedded vector store data directory"
    - "apps/server/src/codebot/config.py — pydantic-settings with CODEBOT_ prefix"
    - "apps/server/src/codebot/db/engine.py — async engine + session factory"
    - "apps/server/src/codebot/db/models/base.py — DeclarativeBase + TimestampMixin"
    - "apps/server/src/codebot/db/models/project.py — Project, Pipeline, PipelinePhase"
    - "apps/server/src/codebot/db/models/agent.py — Agent, AgentExecution"
    - "apps/server/src/codebot/db/models/task.py — Task (self-referential)"
    - "apps/server/src/codebot/db/models/artifact.py — CodeArtifact"
    - "apps/server/src/codebot/db/models/test_result.py — TestResult"
    - "apps/server/src/codebot/db/models/security.py — SecurityFinding (shared Severity enum)"
    - "apps/server/src/codebot/db/models/review.py — ReviewComment"
    - "apps/server/src/codebot/db/models/user.py — User, ApiKey, AuditLog"
    - "apps/server/src/codebot/db/models/event.py — Event (34 EventType values)"
    - "apps/server/src/codebot/db/models/checkpoint.py — Checkpoint (graph resume)"
    - "apps/server/src/codebot/db/models/experiment.py — ExperimentLog (autoresearch metrics)"
    - "apps/server/migrations/versions/68239facb43f_initial_schema.py — initial migration"
    - "apps/server/tests/test_db.py — 8 integration tests"
  modified:
    - "apps/server/src/codebot/db/models/__init__.py — full barrel with all 16 model exports"
    - "apps/server/tests/conftest.py — function-scoped engine for cross-loop safety"
    - "apps/server/pyproject.toml — pytest asyncio_mode=auto config"
decisions:
  - "Port 5433 (not 5432) for PostgreSQL — avoids local port conflict; config.py aligned"
  - "Function-scoped async engine in tests — pytest-asyncio 1.3.0 requires fresh engine per test loop"
  - "LanceDB embedded (no Docker service) — directory at data/lancedb/, excluded from git except .gitkeep"
  - "ExperimentLog added — autoresearch-inspired model for tracking experiment loop results"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-18"
  tasks_completed: 3
  files_created: 20
  files_modified: 3
---

# Phase 01 Plan 02: Docker Stack, LanceDB, ORM Models and Alembic Migration Summary

Docker Compose dev stack (PostgreSQL 16, Redis 7, NATS 2 with JetStream) with 16 SQLAlchemy ORM models, Alembic async migration, and 8 passing integration tests covering CRUD, enums, and FK constraints.

## What Was Built

### Infrastructure (Task 1)
- Docker Compose with 3 core services (postgres:16-alpine on 5433, redis:7-alpine on 6379, nats:2-alpine on 4222/8222) + 2 observability services (langfuse, litellm)
- All services have healthchecks; all 3 core services confirmed healthy at execution time
- `data/lancedb/` directory created with `.gitkeep`; LanceDB is embedded (no Docker service needed)
- `pydantic-settings` configuration with `CODEBOT_` env prefix, `.env` file support

### Database Infrastructure (Task 2a)
- Async SQLAlchemy engine with `pool_size=20, max_overflow=10`
- `DeclarativeBase` with `type_annotation_map` mapping `uuid.UUID → sa.Uuid` and `datetime → sa.DateTime(timezone=True)`
- `TimestampMixin` with `server_default=func.now()` for both `created_at` and `updated_at`
- Alembic initialized with async template; `env.py` overrides DB URL from `settings.database_url`

### ORM Models (Task 2b)
16 tables created by initial migration:

| Model | Table | Key Features |
|---|---|---|
| User | users | email unique, UserRole enum, MFA fields |
| ApiKey | api_keys | key_hash, key_prefix, expires_at |
| AuditLog | audit_logs | immutable, user optional (system actions) |
| Project | projects | ProjectStatus (17 values), ProjectType (4) |
| Pipeline | pipelines | PipelineStatus, graph_definition JSON |
| PipelinePhase | pipeline_phases | PhaseType (14), PhaseStatus (6), approval gate |
| Task | tasks | self-referential FK, TaskStatus (6) |
| Agent | agents | AgentType (30 values), AgentStatus (7) |
| AgentExecution | agent_executions | per-LLM-call record, ExecutionStatus |
| CodeArtifact | code_artifacts | file versioning, git tracking |
| TestResult | test_results | TestStatus, coverage_percent |
| SecurityFinding | security_findings | FindingType (6), Severity (5) |
| ReviewComment | review_comments | reuses Severity, CommentType (6) |
| Event | events | EventType (34 values), project optional |
| Checkpoint | checkpoints | JSON state_data for graph resume |
| ExperimentLog | experiment_logs | ExperimentStatus (5), metric before/after/delta |

### Tests
8 integration tests in `tests/test_db.py`:
1. Alembic version table exists
2. Create and read User
3. Create and read Project with FK to User
4. Create Pipeline linked to Project
5. All ProjectStatus enum values storable
6. Severity enum has all 5 expected values
7. Agent with invalid project_id raises FK error
8. All 16 expected tables exist in public schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pytest-asyncio cross-loop connection error**
- **Found during:** Task 2b test execution
- **Issue:** pytest-asyncio 1.3.0 with `asyncio_mode=auto` creates a new event loop per test function, but the module-level `async_session_factory` was bound to the loop created at import time, causing `RuntimeError: Task got Future attached to a different loop`
- **Fix:** Changed conftest to create a fresh `create_async_engine` per test function (function-scoped fixture), with `pool_size=1, max_overflow=0`. Set `asyncio_default_fixture_loop_scope=function` in pytest config.
- **Files modified:** `apps/server/tests/conftest.py`, `apps/server/pyproject.toml`
- **Commit:** 3e0e75a

**2. [Rule 2 - Missing] pytest config block**
- **Found during:** Task 2b
- **Issue:** No `[tool.pytest.ini_options]` block in `pyproject.toml` — pytest would not run correctly without `asyncio_mode`
- **Fix:** Added `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`, `testpaths = ["tests"]`
- **Files modified:** `apps/server/pyproject.toml`
- **Commit:** 3e0e75a

## Self-Check: PASSED

All key files exist on disk. All 3 commits (1653438, dbcba4f, 3e0e75a) verified in git log. 8 database tests pass.
