---
phase: 2
slug: graph-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (pytest section) |
| **Quick run command** | `uv run pytest tests/unit/graph/ -x -q` |
| **Full suite command** | `uv run pytest tests/unit/graph/ tests/integration/graph/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/graph/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/unit/graph/ tests/integration/graph/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | GRPH-01 | unit | `uv run pytest tests/unit/graph/test_models.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | GRPH-02 | unit | `uv run pytest tests/unit/graph/test_yaml_loader.py -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | GRPH-03 | unit | `uv run pytest tests/unit/graph/test_validator.py -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | GRPH-04 | unit | `uv run pytest tests/unit/graph/test_compiler.py -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | GRPH-05 | unit | `uv run pytest tests/unit/graph/test_shared_state.py -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | GRPH-07 | unit | `uv run pytest tests/unit/graph/test_parallel.py -x` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 2 | GRPH-08 | unit | `uv run pytest tests/unit/graph/test_switch.py -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 1 | GRPH-06 | integration | `uv run pytest tests/integration/graph/test_checkpoint.py -x` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 1 | GRPH-09 | unit | `uv run pytest tests/unit/graph/test_tracing.py -x` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 2 | GRPH-10 | integration | `uv run pytest tests/integration/graph/test_dynamic_fanout.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/graph/` — directory structure for graph engine unit tests
- [ ] `tests/integration/graph/` — directory structure for integration tests
- [ ] `tests/unit/graph/conftest.py` — shared fixtures (mock graph definitions, sample YAML)
- [ ] `tests/integration/graph/conftest.py` — integration fixtures (PostgreSQL test connection)
- [ ] pytest + pytest-asyncio installed via `uv add --dev pytest pytest-asyncio`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Graph visualization renders in dashboard | GRPH-04 (partial) | Requires browser rendering | Load graph in React Flow, verify node/edge display |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
