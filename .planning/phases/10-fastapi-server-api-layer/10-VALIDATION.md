---
phase: 10
slug: fastapi-server-api-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x with httpx.AsyncClient |
| **Config file** | `pyproject.toml` [tool.pytest] section |
| **Quick run command** | `uv run pytest tests/unit/server/api/ -x -q` |
| **Full suite command** | `uv run pytest tests/unit/server/api/ tests/integration/server/api/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/server/api/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/unit/server/api/ tests/integration/server/api/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | SRVR-01 | unit | `uv run pytest tests/unit/server/api/test_projects.py -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | SRVR-01 | unit | `uv run pytest tests/unit/server/api/test_pipelines.py -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | SRVR-02 | unit+integration | `uv run pytest tests/unit/server/api/test_websocket.py -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 01 | 1 | SRVR-03 | unit | `uv run pytest tests/unit/server/api/test_auth.py -x` | ❌ W0 | ⬜ pending |
| 10-04-01 | 01 | 1 | SRVR-04 | unit | `uv run pytest tests/unit/server/api/test_pipeline_config.py -x` | ❌ W0 | ⬜ pending |
| 10-05-01 | 02 | 2 | SRVR-05 | unit | `uv run pytest tests/unit/server/api/test_agents.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/server/api/conftest.py` — shared fixtures (async client, test DB, mock NATS)
- [ ] `tests/unit/server/api/test_projects.py` — stubs for SRVR-01 project CRUD
- [ ] `tests/unit/server/api/test_pipelines.py` — stubs for SRVR-01 pipeline control
- [ ] `tests/unit/server/api/test_websocket.py` — stubs for SRVR-02 WebSocket events
- [ ] `tests/unit/server/api/test_auth.py` — stubs for SRVR-03 auth/authz
- [ ] `tests/unit/server/api/test_pipeline_config.py` — stubs for SRVR-04 preset config
- [ ] `tests/unit/server/api/test_agents.py` — stubs for SRVR-05 agent management

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WebSocket reconnection | SRVR-02 | Requires network interruption simulation | Disconnect client mid-stream, verify auto-reconnect and event replay |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
