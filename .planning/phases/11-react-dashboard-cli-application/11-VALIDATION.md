---
phase: 11
slug: react-dashboard-cli-application
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (dashboard), pytest 7.x (CLI + creator agents) |
| **Config file** | `apps/dashboard/vitest.config.ts`, `pyproject.toml [tool.pytest]` |
| **Quick run command** | `pnpm -F dashboard test -- --run` and `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `pnpm -F dashboard test -- --run --coverage` and `uv run pytest tests/ -q` |
| **Estimated runtime** | ~45 seconds (dashboard: ~20s, CLI+agents: ~25s) |

---

## Sampling Rate

- **After every task commit:** Run `pnpm -F dashboard test -- --run` or `uv run pytest tests/unit/ -x -q`
- **After every plan wave:** Run full suite commands
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DASH-01 | unit | `pnpm -F dashboard test -- pipeline-view` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | DASH-06 | integration | `pnpm -F dashboard test -- use-socket` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | DASH-01 | unit | `pnpm -F dashboard test -- agent-node` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | CLI-01 | unit | `uv run pytest tests/unit/cli/test_project.py` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | CLI-02 | unit | `uv run pytest tests/unit/cli/test_pipeline.py` | ❌ W0 | ⬜ pending |
| 11-02-03 | 02 | 1 | CLI-03 | integration | `uv run pytest tests/integration/cli/test_streaming.py` | ❌ W0 | ⬜ pending |
| 11-02-04 | 02 | 1 | CLI-04 | unit | `uv run pytest tests/unit/cli/test_config.py` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 2 | DASH-02 | unit | `pnpm -F dashboard test -- agent-panel` | ❌ W0 | ⬜ pending |
| 11-03-02 | 03 | 2 | DASH-03 | unit | `pnpm -F dashboard test -- code-editor` | ❌ W0 | ⬜ pending |
| 11-03-03 | 03 | 2 | DASH-04 | unit | `pnpm -F dashboard test -- terminal-panel` | ❌ W0 | ⬜ pending |
| 11-03-04 | 03 | 2 | DASH-05 | integration | `pnpm -F dashboard test -- collab` | ❌ W0 | ⬜ pending |
| 11-03-05 | 03 | 2 | DASH-07 | unit | `pnpm -F dashboard test -- cost-breakdown` | ❌ W0 | ⬜ pending |
| 11-03-06 | 03 | 2 | DASH-08 | unit | `pnpm -F dashboard test -- preview-frame` | ❌ W0 | ⬜ pending |
| 11-03-07 | 03 | 2 | AGNT-09 | unit | `uv run pytest tests/unit/agents/test_skill_creator.py` | ❌ W0 | ⬜ pending |
| 11-03-08 | 03 | 2 | AGNT-10 | unit | `uv run pytest tests/unit/agents/test_hooks_creator.py` | ❌ W0 | ⬜ pending |
| 11-03-09 | 03 | 2 | AGNT-11 | unit | `uv run pytest tests/unit/agents/test_tools_creator.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/dashboard/vitest.config.ts` — Vitest config with React Testing Library
- [ ] `apps/dashboard/src/test/setup.ts` — test setup (jsdom, mock Socket.IO)
- [ ] `tests/unit/cli/conftest.py` — CLI test fixtures (Click CliRunner, mock API)
- [ ] `tests/unit/agents/conftest.py` — Agent test fixtures (mock LLM, mock registries)

*If none: "Existing infrastructure covers all phase requirements."*

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
