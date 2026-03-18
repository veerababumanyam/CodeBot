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
| **Framework** | pytest 8.x with httpx.AsyncClient |
| **Config file** | `apps/server/pyproject.toml` [tool.pytest.ini_options] section |
| **Quick run command** | `cd apps/server && uv run pytest tests/api/ -x -q` |
| **Full suite command** | `cd apps/server && uv run pytest tests/api/ tests/websocket/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/server && uv run pytest tests/api/ -x -q`
- **After every plan wave:** Run `cd apps/server && uv run pytest tests/api/ tests/websocket/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | SRVR-03 | unit | `cd apps/server && uv run pytest tests/api/test_auth.py -x` | No -- W0 | pending |
| 10-01-02 | 01 | 1 | SRVR-01 | unit | `cd apps/server && uv run pytest tests/api/test_projects.py -x` | No -- W0 | pending |
| 10-02-01 | 02 | 2 | SRVR-04 | integration | `cd apps/server && uv run pytest tests/api/test_pipelines.py -x` | No -- W0 | pending |
| 10-02-02 | 02 | 2 | SRVR-05 | integration | `cd apps/server && uv run pytest tests/api/test_agents.py -x` | No -- W0 | pending |
| 10-02-03 | 02 | 2 | SRVR-02 | unit+integration | `cd apps/server && uv run pytest tests/websocket/ -x` | No -- W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `apps/server/tests/api/__init__.py` -- test package
- [ ] `apps/server/tests/api/conftest.py` -- shared fixtures (async client, auth headers, test user factory)
- [ ] `apps/server/tests/api/test_auth.py` -- covers SRVR-03 (auth, RBAC, API keys)
- [ ] `apps/server/tests/api/test_projects.py` -- covers SRVR-01 (project CRUD)
- [ ] `apps/server/tests/api/test_pipelines.py` -- covers SRVR-01 (pipeline lifecycle), SRVR-04 (preset selection)
- [ ] `apps/server/tests/api/test_agents.py` -- covers SRVR-05 (agent start/stop/restart/configure)
- [ ] `apps/server/tests/websocket/__init__.py` -- test package
- [ ] `apps/server/tests/websocket/test_manager.py` -- covers SRVR-02 (WebSocket connection, JWT auth)
- [ ] `apps/server/tests/websocket/test_bridge.py` -- covers SRVR-02 (NATS event forwarding)

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
