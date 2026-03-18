---
phase: 9
slug: full-agent-roster
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 9 -- Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` `[tool.pytest]` section |
| **Quick run command** | `uv run pytest tests/unit/agents/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest tests/unit/agents/ tests/integration/agents/ -v --timeout=60` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/agents/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/unit/agents/ tests/integration/agents/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | AGNT-08 | unit | `uv run pytest tests/unit/agents/test_agent_registry.py -v` | W0 | pending |
| 09-01-02 | 01 | 1 | BRST-01..07 | unit | `uv run pytest tests/unit/agents/test_brainstorming.py -v` | W0 | pending |
| 09-01-03 | 01 | 1 | RSRC-01..04 | unit | `uv run pytest tests/unit/agents/test_researcher.py -v` | W0 | pending |
| 09-02-01 | 02 | 1 | ARCH-01..06 | unit | `uv run pytest tests/unit/agents/test_architecture_agents.py -v` | W0 | pending |
| 09-02-02 | 02 | 1 | PLAN-01..03 | unit | `uv run pytest tests/unit/agents/test_planning_agents.py -v` | W0 | pending |
| 09-03-01 | 03 | 2 | IMPL-01,03,04 | unit | `uv run pytest tests/unit/agents/test_implementation_agents.py -v` | W0 | pending |
| 09-04-01 | 04 | 2 | QA-02..05,07 | unit | `uv run pytest tests/unit/agents/test_qa_agents.py -v` | W0 | pending |
| 09-04-02 | 04 | 2 | TEST-03,04 | unit | `uv run pytest tests/unit/agents/test_testing_agents.py -v` | W0 | pending |
| 09-05-01 | 05 | 3 | DOCS-01..04 | unit | `uv run pytest tests/unit/agents/test_doc_writer.py tests/unit/agents/test_remaining_agents.py -v` | W0 | pending |
| 09-05-02 | 05 | 3 | AGNT-08 | integration | `uv run pytest tests/integration/agents/test_agent_registry.py -v` | W0 | pending |
| 09-05-03 | 05 | 3 | EVNT-02..04 | integration | `uv run pytest tests/integration/agents/test_event_audit.py -v` | W0 | pending |

*Status: pending -- green -- red -- flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/agents/conftest.py` -- shared agent fixtures (mock LLM, mock tools, mock context)
- [ ] `tests/unit/agents/test_agent_registry.py` -- tests for AgentRegistry register/create/list
- [ ] `tests/unit/agents/test_brainstorming.py` -- stubs for BRST-01..07
- [ ] `tests/unit/agents/test_researcher.py` -- stubs for RSRC-01..04
- [ ] `tests/unit/agents/test_architecture_agents.py` -- stubs for ARCH-01..06
- [ ] `tests/unit/agents/test_planning_agents.py` -- stubs for PLAN-01..03
- [ ] `tests/unit/agents/test_implementation_agents.py` -- stubs for IMPL-01,03,04
- [ ] `tests/unit/agents/test_qa_agents.py` -- stubs for QA-02..05,07
- [ ] `tests/unit/agents/test_testing_agents.py` -- stubs for TEST-03,04
- [ ] `tests/unit/agents/test_doc_writer.py` -- stubs for DOCS-01..04
- [ ] `tests/unit/agents/test_remaining_agents.py` -- stubs for remaining 10 agents
- [ ] `tests/integration/agents/test_agent_registry.py` -- stubs for AGNT-08 (all 30 registered)
- [ ] `tests/integration/agents/test_event_audit.py` -- stubs for EVNT-02..04

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent system prompts produce quality output | BRST-01, ARCH-01 | LLM output quality is subjective | Review sample outputs against AGENT_CATALOG expectations |
| Parallel agent worktree isolation | IMPL-01 | Requires git worktree runtime | Run S5 subgraph with 2+ agents, verify separate worktrees created |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
