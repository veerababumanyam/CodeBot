---
phase: 01-foundation-and-scaffolding
plan: "01"
subsystem: infra
tags: [turborepo, uv, pnpm, monorepo, fastapi, react, vite, typescript, python]

# Dependency graph
requires: []
provides:
  - "Turborepo monorepo with 6 workspace packages (apps/server, apps/dashboard, apps/cli, libs/agent-sdk, libs/shared-types, libs/graph-engine)"
  - "Root pyproject.toml with uv workspace (Python 3.12+, ruff, mypy strict, pytest async)"
  - "Root package.json with pnpm workspace and turbo devDeps only (no stale deps)"
  - "pnpm-workspace.yaml, turbo.json, Makefile, .gitignore, .env.example, .pre-commit-config.yaml"
  - "FastAPI skeleton app with /health endpoint"
  - "React/Vite dashboard skeleton"
  - "TypeScript CLI skeleton with commander"
  - "Python stubs: agent-sdk, graph-engine"
  - "TypeScript shared-types lib with declaration output"
  - "configs/ directory structure (pipelines/, agents/, providers/)"
affects:
  - 01-foundation-and-scaffolding
  - all subsequent phases

# Tech tracking
tech-stack:
  added:
    - "uv (Python package manager, workspace mode)"
    - "pnpm 9.14.0 (Node package manager, workspace mode)"
    - "Turborepo ^2.3.0 (polyglot monorepo build orchestration)"
    - "FastAPI >=0.115.0 (Python web framework)"
    - "React >=18.3.0 + Vite >=6.0.0 (dashboard SPA)"
    - "TypeScript ^5.6.0 (strict ESM-only)"
    - "commander ^12.1.0 (CLI framework)"
    - "ruff 0.7+ (Python linter + formatter)"
    - "mypy 1.13+ strict (Python type checker)"
  patterns:
    - "Pattern: Python packages use package.json Turborepo shims delegating scripts to uv run"
    - "Pattern: TypeScript strict mode with noUncheckedIndexedAccess + exactOptionalPropertyTypes + verbatimModuleSyntax"
    - "Pattern: Root package.json devDeps only (turbo, typescript) — no hoisted workspace deps"

key-files:
  created:
    - pyproject.toml
    - package.json
    - pnpm-workspace.yaml
    - turbo.json
    - Makefile
    - .gitignore
    - .env.example
    - .pre-commit-config.yaml
    - apps/server/pyproject.toml
    - apps/server/package.json
    - apps/server/src/codebot/__init__.py
    - apps/server/src/codebot/main.py
    - apps/dashboard/package.json
    - apps/dashboard/tsconfig.json
    - apps/dashboard/vite.config.ts
    - apps/dashboard/index.html
    - apps/dashboard/src/main.tsx
    - apps/cli/package.json
    - apps/cli/tsconfig.json
    - apps/cli/src/index.ts
    - libs/agent-sdk/pyproject.toml
    - libs/agent-sdk/package.json
    - libs/agent-sdk/src/agent_sdk/__init__.py
    - libs/shared-types/package.json
    - libs/shared-types/tsconfig.json
    - libs/shared-types/src/index.ts
    - libs/graph-engine/pyproject.toml
    - libs/graph-engine/package.json
    - libs/graph-engine/src/graph_engine/__init__.py
    - configs/pipelines/.gitkeep
    - configs/agents/.gitkeep
    - configs/providers/.gitkeep
    - uv.lock
    - pnpm-lock.yaml
  modified:
    - pyproject.toml (replaced stale py311 version)
    - package.json (replaced stale next/yjs/tremor/eslint deps)

key-decisions:
  - "Replaced stale root pyproject.toml (py311) with clean py312+ uv workspace config per research pitfall"
  - "Replaced stale root package.json (next, yjs, tremor, eslint hoisted) with clean devDeps-only config"
  - "Python packages get package.json shims — scripts delegate to uv run for Turborepo discovery"
  - "apps/dashboard uses moduleResolution=bundler (Vite), apps/cli uses NodeNext (Node.js runtime)"

patterns-established:
  - "Python workspace shim pattern: package.json with uv-delegating scripts alongside pyproject.toml"
  - "TypeScript strict baseline: noUncheckedIndexedAccess + exactOptionalPropertyTypes + verbatimModuleSyntax"
  - "Root package.json: devDeps only (turbo, typescript) — all app deps stay in workspace packages"

requirements-completed:
  - REQ-001

# Metrics
duration: 4min
completed: "2026-03-18"
---

# Phase 1 Plan 01: Monorepo Scaffolding Summary

**Turborepo monorepo with 6 pnpm/uv workspaces, clean Python 3.12+ uv workspace root, and turbo build passing all 6 packages from scratch**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T06:57:50Z
- **Completed:** 2026-03-18T07:01:40Z
- **Tasks:** 2
- **Files modified:** 35

## Accomplishments
- All 6 workspace packages exist with valid configurations discoverable by Turborepo
- `uv sync && pnpm install && pnpm turbo build` all succeed with zero errors
- Replaced stale root configs (py311, next.js, yjs, tremor, eslint) with clean design-aligned versions
- FastAPI /health skeleton, React/Vite dashboard, TypeScript CLI stub all compile cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create root configs and workspace declarations** - `853f88e` (chore)
2. **Task 2: Create all workspace packages with configs and stubs** - `a6a60d3` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified

- `pyproject.toml` - Root uv workspace: Python 3.12+, ruff py312, mypy strict, pytest async
- `package.json` - Root pnpm: turbo+typescript devDeps only, no stale deps (next/yjs/tremor removed)
- `pnpm-workspace.yaml` - Declares apps/*, libs/*, sdks/* workspaces
- `turbo.json` - Task pipeline: build, test, lint, typecheck, dev, migrate, format
- `Makefile` - dev, build, test, lint, typecheck, migrate, docker-up/down, clean, install
- `.gitignore` - Python, Node, IDE, env, Docker, OS entries
- `.env.example` - CODEBOT_DATABASE_URL, CODEBOT_REDIS_URL, CODEBOT_NATS_URL, CODEBOT_DEBUG, CODEBOT_LOG_LEVEL
- `.pre-commit-config.yaml` - ruff (format+lint) and mypy hooks
- `apps/server/pyproject.toml` - codebot-server with fastapi, sqlalchemy, asyncpg, pydantic, nats-py, redis
- `apps/server/package.json` - Turborepo shim delegating scripts to uv run
- `apps/server/src/codebot/main.py` - FastAPI app with /health endpoint
- `apps/dashboard/package.json` - React 18.3+, Vite 6, TypeScript devDeps
- `apps/dashboard/tsconfig.json` - Strict: noUncheckedIndexedAccess, exactOptionalPropertyTypes, verbatimModuleSyntax
- `apps/dashboard/vite.config.ts` - React plugin, port 3000
- `apps/dashboard/src/main.tsx` - Minimal React app rendering CodeBot Dashboard
- `apps/cli/package.json` - commander dep, type:module, bin codebot
- `apps/cli/tsconfig.json` - NodeNext module resolution, outDir dist
- `apps/cli/src/index.ts` - Minimal commander CLI with --version and --help
- `libs/agent-sdk/pyproject.toml` - agent-sdk Python package with pydantic dep
- `libs/shared-types/tsconfig.json` - Declaration output: dist/index.d.ts
- `libs/shared-types/src/index.ts` - Placeholder export (populated in plan 01-03)
- `libs/graph-engine/pyproject.toml` - graph-engine Python package stub
- `uv.lock` - Python lockfile (48 packages)
- `pnpm-lock.yaml` - Node lockfile (75 packages)

## Decisions Made
- Replaced stale root pyproject.toml (targets py311) and package.json (includes next/yjs/tremor/eslint) per research pitfall documentation — created clean configs from scratch
- Python packages use package.json shims (Turborepo pattern) where scripts echo or delegate to `uv run`
- `apps/dashboard/tsconfig.json` uses `moduleResolution: bundler` (Vite environment); `apps/cli/tsconfig.json` uses `moduleResolution: NodeNext` (Node.js runtime)
- Root `package.json` has devDependencies only (turbo, typescript) — no hoisted workspace deps

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all commands succeeded cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Monorepo scaffold complete; Plan 01-02 (Docker Compose infrastructure) and Plan 01-03 (database schemas + shared types) can both proceed
- uv.lock and pnpm-lock.yaml committed — clean installs are reproducible
- Python workspace members: apps/server, libs/agent-sdk, libs/graph-engine

## Self-Check: PASSED

All key files verified present:
- pyproject.toml, package.json, pnpm-workspace.yaml, turbo.json: FOUND
- apps/server/src/codebot/main.py: FOUND
- apps/dashboard/src/main.tsx: FOUND
- libs/shared-types/src/index.ts: FOUND
- .planning/phases/01-foundation-and-scaffolding/01-01-SUMMARY.md: FOUND

All commits verified:
- 853f88e (chore: root configs): FOUND
- a6a60d3 (feat: workspace packages): FOUND

---
*Phase: 01-foundation-and-scaffolding*
*Completed: 2026-03-18*
