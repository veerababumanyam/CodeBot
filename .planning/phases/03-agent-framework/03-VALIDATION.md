---
phase: 3
slug: agent-framework
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/unit/agents/ -x -q` |
| **Full suite command** | `uv run pytest tests/unit/agents/ tests/integration/agents/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/agents/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/unit/agents/ tests/integration/agents/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| *Populated after planning* | | | | | | | |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/agents/test_base_agent.py` — stubs for AGNT-01, AGNT-02, AGNT-03
- [ ] `tests/unit/agents/test_agent_node.py` — stubs for AGNT-05, AGNT-06
- [ ] `tests/unit/agents/test_agent_config.py` — stubs for AGNT-07
- [ ] `tests/unit/agents/test_agent_recovery.py` — stubs for AGNT-12
- [ ] `tests/unit/agents/conftest.py` — shared fixtures (mock LLM, mock context)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| State transition logging visibility | AGNT-04 | Log output format requires visual inspection | Run agent, check structured logs for state transitions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
