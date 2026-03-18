---
phase: 1
slug: foundation-and-scaffolding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 1 -- Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python) + Vitest (TypeScript) |
| **Config file** | `pyproject.toml` (pytest section) + `vitest.config.ts` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ && pnpm -F shared-types test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ && pnpm -F shared-types test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | REQ-001 | build | `turbo build` | -- W0 | pending |
| 1-01-02 | 01 | 1 | REQ-001 | build | `uv sync && pnpm install` | -- W0 | pending |
| 1-02-01 | 02 | 2 | REQ-002 | integration | `docker-compose up -d && docker-compose exec postgres pg_isready -U codebot && docker-compose exec redis redis-cli ping && curl -sf http://localhost:8222/healthz` | -- W0 | pending |
| 1-02-2a | 02 | 2 | REQ-003 | unit | `uv run python -c "from codebot.db.engine import engine, async_session_factory; print('OK')"` | -- W0 | pending |
| 1-02-2b | 02 | 2 | REQ-003 | integration | `uv run alembic upgrade head && uv run pytest tests/test_db.py -x -v --timeout=30` | -- W0 | pending |
| 1-03-01 | 03 | 3 | REQ-004 | unit | `uv run pytest apps/server/tests/test_models.py -x -v --timeout=30` | -- W0 | pending |
| 1-03-02 | 03 | 3 | REQ-005 | integration | `uv run pytest apps/server/tests/test_events.py -x -v --timeout=30` | -- W0 | pending |
| 1-03-03 | 03 | 3 | REQ-004 | build | `pnpm -F shared-types build` | -- W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` -- shared fixtures for database, NATS connections
- [ ] `tests/test_models.py` -- stubs for Pydantic model validation (REQ-004)
- [ ] `tests/test_events.py` -- stubs for NATS JetStream pub/sub (REQ-005)
- [ ] `pytest` + `pytest-asyncio` -- install test framework

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker services accessible | REQ-002 | Requires running Docker daemon | Run `docker-compose up -d`, verify all containers healthy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
