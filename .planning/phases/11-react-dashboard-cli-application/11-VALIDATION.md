---
phase: 11
slug: react-dashboard-cli-application
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-18
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (dashboard + CLI), pytest 7.x (creator agents) |
| **Config file** | `apps/dashboard/vitest.config.ts`, `apps/cli/vitest.config.ts`, `pyproject.toml [tool.pytest]` |
| **Quick run command** | `pnpm -F dashboard test -- --run` and `pnpm -F cli test -- --run` and `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `pnpm -F dashboard test -- --run --coverage` and `pnpm -F cli test -- --run --coverage` and `uv run pytest tests/ -q` |
| **Estimated runtime** | ~45 seconds (dashboard: ~20s, CLI: ~10s, agents: ~15s) |

---

## Sampling Rate

- **After every task commit:** Run quick command for affected workspace
- **After every plan wave:** Run full suite commands
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DASH-01, DASH-06 | unit | `pnpm -F dashboard test -- pipeline-view` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | DASH-01, DASH-06 | integration | `pnpm -F dashboard test -- --run` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | CLI-01 | unit | `pnpm -F cli test -- project` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | CLI-02, CLI-03, CLI-04 | unit | `pnpm -F cli test -- --run` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 2 | DASH-02, DASH-07 | unit | `pnpm -F dashboard test -- agent-panel` | ❌ W0 | ⬜ pending |
| 11-03-02 | 03 | 2 | DASH-03, DASH-04, DASH-05, DASH-08 | unit | `pnpm -F dashboard test -- code-editor` | ❌ W0 | ⬜ pending |
| 11-04-01 | 04 | 1 | AGNT-09, AGNT-10 | unit | `uv run pytest tests/unit/agents/test_skill_creator.py tests/unit/agents/test_hooks_creator.py` | ❌ W0 | ⬜ pending |
| 11-04-02 | 04 | 1 | AGNT-11 | unit | `uv run pytest tests/unit/agents/test_tools_creator.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/dashboard/vitest.config.ts` — Vitest config with React Testing Library (created inline by Plan 11-01 Task 1)
- [ ] `apps/dashboard/src/test/setup.ts` — test setup with jsdom, mock Socket.IO (created inline by Plan 11-01 Task 1)
- [ ] `apps/cli/vitest.config.ts` — Vitest config for CLI tests (created inline by Plan 11-02 Task 1)
- [ ] `apps/cli/tests/setup.ts` — CLI test setup with fetch mocks (created inline by Plan 11-02 Task 1)
- [ ] Agent test fixtures — defined inline in Plan 11-04 test files

*Wave 0 infrastructure is created inline within Wave 1 tasks (Plan 11-01 and 11-02 create test configs before running tests).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| React Flow graph is visually readable at 30+ nodes | DASH-01 | Visual layout quality | Load test graph with 30 nodes, verify no overlap, readable labels |
| Monaco editor provides syntax highlighting and IntelliSense | DASH-03 | Visual + interactive behavior | Open a .py file in editor, verify highlighting and autocomplete |
| xterm.js terminal renders ANSI colors correctly | DASH-04 | Visual rendering | Stream colored agent logs, verify color accuracy |
| Live preview iframe loads target application | DASH-08 | Requires running sandbox | Start pipeline, verify iframe shows running app |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
