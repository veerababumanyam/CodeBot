---
phase: 3
slug: agent-framework
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` (per-library) |
| **Quick run command** | `cd libs/agent-sdk && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd libs/agent-sdk && uv run pytest tests/ -v && cd ../../libs/graph-engine && uv run pytest tests/ -v && cd ../../apps/server && uv run pytest tests/test_agent_loader.py -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command for the relevant library
- **After every plan wave:** Run full suite command across all three packages
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | AGNT-03, AGNT-07, AGNT-12 | unit | `cd libs/agent-sdk && uv run pytest tests/test_state_machine.py tests/test_recovery.py tests/test_metrics.py -v --tb=short` | W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | AGNT-01, AGNT-05, AGNT-06 | unit | `cd libs/agent-sdk && uv run pytest tests/ -v --tb=short` | W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | AGNT-02, AGNT-04, AGNT-12 | unit | `cd libs/graph-engine && uv run pytest tests/test_agent_node.py -v --tb=short` | W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | AGNT-05 | unit | `cd apps/server && uv run pytest tests/test_agent_loader.py -v --tb=short` | W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `libs/agent-sdk/tests/test_state_machine.py` — stubs for AGNT-03
- [ ] `libs/agent-sdk/tests/test_recovery.py` — stubs for AGNT-07
- [ ] `libs/agent-sdk/tests/test_metrics.py` — stubs for AGNT-12
- [ ] `libs/agent-sdk/tests/test_base_agent.py` — stubs for AGNT-01, AGNT-06
- [ ] `libs/agent-sdk/tests/test_agent_config.py` — stubs for AGNT-05
- [ ] `libs/agent-sdk/tests/conftest.py` — shared fixtures (mock LLM, mock context)
- [ ] `libs/graph-engine/tests/test_agent_node.py` — stubs for AGNT-02, AGNT-04
- [ ] `libs/graph-engine/tests/conftest.py` — shared fixtures (test agents)
- [ ] `apps/server/tests/test_agent_loader.py` — stubs for AGNT-05

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| State transition logging visibility | AGNT-04 | Log output format requires visual inspection | Run agent, check structured logs for state transitions |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-18
