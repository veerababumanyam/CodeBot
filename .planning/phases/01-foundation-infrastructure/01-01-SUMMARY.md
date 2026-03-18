---
phase: 01-foundation-infrastructure
plan: 01
subsystem: infrastructure
tags: [monorepo, docker, postgresql, redis, nats, sqlalchemy, fastapi, agent-sdk]

requires:
  - phase: none
    provides: greenfield project
provides:
  - Monorepo with apps/server, apps/dashboard, apps/cli, libs/agent-sdk, libs/graph-engine
  - Docker Compose stack with PostgreSQL 16, Redis 7, NATS 2 (JetStream), Langfuse
  - FastAPI server entrypoint (main.py) with config module
  - SQLAlchemy DeclarativeBase with 13 domain models (project, agent, task, artifact, event, review, security, checkpoint, experiment, test_result, user, plus base and __init__)
  - Agent SDK shared models (agent, enums, events, pipeline, project, task)
  - YAML config directories (agents, pipelines, providers)
  - Turborepo + pnpm Node workspace, uv Python workspace
  - Makefile with common commands
---

<one_liner>
Monorepo scaffolding, Docker stack (PostgreSQL/Redis/NATS/Langfuse), 13 SQLAlchemy models, agent SDK types, and config structure — all foundation infrastructure.
</one_liner>

<changes>
## Monorepo Structure
- Created `apps/server/`, `apps/dashboard/`, `apps/cli/` application directories
- Created `libs/agent-sdk/`, `libs/graph-engine/` shared library directories
- Created `configs/agents/`, `configs/pipelines/`, `configs/providers/` YAML config dirs
- Set up `pyproject.toml` (Python/uv), `package.json` + `turbo.json` (Node/pnpm/Turborepo)
- Added `Makefile` with common development commands

## Docker Development Stack
- `docker-compose.yml` with 4 services:
  - PostgreSQL 16 Alpine (port 5432) with health check
  - Redis 7 Alpine (port 6379) with 256MB LRU eviction
  - NATS 2 Alpine with JetStream enabled (ports 4222/8222)
  - Langfuse (port 3001) for LLM observability

## Database Schema (SQLAlchemy 2.0)
- `db/models/base.py` — DeclarativeBase with UUID PK, timestamp mixins
- 13 domain models: project, agent, task, artifact, event, review, security, checkpoint, experiment, test_result, user

## Agent SDK
- Shared Pydantic models: agent, enums, events, pipeline, project, task
- Used by both server and graph engine

## Server
- `main.py` — FastAPI entrypoint
- `config.py` — Application configuration
- `events/` — Event system foundation
</changes>

<gotchas>
- Phase 1 was completed before GSD tracking was adopted; this summary was created retroactively
- NATS JetStream is enabled via Docker command flags, not application-level config
- Langfuse depends on the same PostgreSQL instance (separate database)
</gotchas>
