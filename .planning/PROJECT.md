# CodeBot

## What This Is

CodeBot is an autonomous, end-to-end software development platform powered by a graph-centric multi-agent system of ~30 specialized AI agents. It transforms natural language ideas, PRDs, or existing codebases into fully tested, reviewed, secured, documented, and cloud-deployed applications across web, mobile (React Native), and backend platforms — with zero manual coding required. The platform covers the complete SDLC from brainstorming through production deployment, supporting greenfield, inflight, brownfield, and autonomous improvement (Improve mode) projects.

## Core Value

A single command transforms a spark of an idea into a production-grade, deployed, multi-platform application — autonomously orchestrating 30 AI agents across brainstorming, research, architecture, planning, implementation, review, testing, debugging, documentation, and deployment.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Graph-centric multi-agent orchestration engine (MASFactory-inspired DAG execution)
- [ ] 11-stage SDLC pipeline (S0 Project Init through S10 Deployment)
- [ ] ~30 specialized AI agents with role-specific prompts and tool access
- [ ] Multi-LLM support: Claude Code, OpenAI Codex, Google Gemini, Ollama, LM Studio
- [ ] Intelligent model routing (task-based, complexity-based, privacy-based, cost-based, latency-based)
- [ ] CLI agent integration (Claude Code SDK, Codex CLI subprocess, Gemini CLI subprocess)
- [ ] 3-tier context management (L0 always-loaded, L1 on-demand, L2 deep retrieval)
- [ ] Episodic memory with cross-session and cross-project learning
- [ ] Vector store (ChromaDB) with Tree-sitter code indexing
- [ ] Git worktree isolation per coding agent
- [ ] Sandboxed code execution (containerized per agent, gVisor/Kata isolation)
- [ ] Live preview (hot-reload, mobile viewport emulation, VNC for desktop apps)
- [ ] Web dashboard (React/Vite/TypeScript/Tailwind): pipeline view, agent activity, code viewer, test results, deployment status, brainstorming board, template gallery, tech stack configurator, cost tracker, knowledge base browser, architecture visualizer, git timeline
- [ ] CLI interface (TypeScript): all core commands (init, brainstorm, plan, start, status, review, deploy, config, etc.)
- [ ] IDE extensions (VS Code, JetBrains, Neovim, Cursor)
- [ ] 4 project modes: greenfield, inflight, brownfield, improve (autonomous optimization)
- [ ] Brainstorming phase: idea exploration, competitive analysis, feature prioritization, scope definition
- [ ] Research phase: technology research, pattern discovery, dependency analysis, API discovery
- [ ] Architecture phase (parallel): system architecture (C4), database design, API design, UI/UX design
- [ ] Planning phase: task decomposition, dependency graphs, topological ordering, resource allocation
- [ ] Implementation phase (parallel worktrees): frontend, backend, middleware, mobile (React Native), infrastructure, integrations
- [ ] Quality assurance phase (parallel): code review, security audit (Semgrep, SonarQube, Trivy, Gitleaks), accessibility (WCAG 2.1), i18n/L10n, performance analysis
- [ ] Testing phase (parallel suites): unit, integration, E2E (Playwright), UI component, visual regression, smoke, performance (k6), security (ZAP), accessibility (axe-core), API contract (Pact), cross-browser, mobile device, mutation, chaos (optional)
- [ ] Debug & fix cycle: root cause analysis, automated fix generation, regression testing, cross-platform fix propagation
- [ ] Documentation phase: API docs, README, ADRs, deployment guides, runbooks
- [ ] Agent learning: skill creation, hook creation, tool creation, pattern library, anti-pattern registry
- [ ] Deployment phase (S10): CI/CD generation, multi-cloud (AWS, GCP, Azure, Vercel, Railway, Netlify, Fly.io, DigitalOcean), iOS App Store, Google Play Store, multi-environment management, rollback automation, monitoring setup
- [ ] Responsive web design across all generated applications
- [ ] React Native cross-platform mobile development
- [ ] Multi-repo support with cross-repo dependency management
- [ ] Template system: Material Design, Ant Design, Tailwind UI, Shadcn/ui, Chakra UI, Bootstrap, custom
- [ ] Cost intelligence: per-agent token tracking, per-stage costs, budget limits, cloud cost estimation
- [ ] Agent safety guardrails: sandboxed creation, review before activation, capability boundaries
- [ ] Self-healing: automatic dependency resolution, config auto-fix, test flakiness detection, LLM fallback chains, pipeline resume from checkpoint
- [ ] Communication protocol: state flow, message flow, control flow, event flow, broadcast flow
- [ ] Human-in-the-loop approval gates at configurable checkpoints
- [ ] Multi-modal input: text, images, diagrams, voice (transcribed), video walkthroughs, reference URLs

### Out of Scope

- Real-time CRDT collaboration (humans + agents editing simultaneously) — Deferred to v2. High complexity, not required for core autonomous pipeline value proposition
- vLLM, LocalAI, llama.cpp, TGI, Text Generation WebUI — Deferred. Ollama and LM Studio cover self-hosted needs for v1
- Aider and Continue CLI integrations — Deferred. Claude Code, Codex, and Gemini CLI cover primary needs
- Native iOS (Swift/SwiftUI) and Native Android (Kotlin/Compose) — Deferred. React Native covers cross-platform mobile for v1
- Flutter support — Deferred. React Native is the v1 mobile strategy
- Voice/Video integration for collaboration — Deferred to v2 with CRDT collab

## Context

- **Current state:** Documentation and design phase only — no source code exists yet. Comprehensive docs in `docs/` covering PRD v2.5, architecture, system design, agent catalog, API spec, workflows, technical requirements, data models, project structure, and research summary
- **Paradigm:** Based on MASFactory framework (arXiv:2603.06007) — multi-agent workflows modeled as directed computation graphs
- **Tech stack (planned):** Python 3.12+ (FastAPI, SQLAlchemy, asyncio TaskGroup) for backend/orchestration; React (Vite) + TypeScript 5.5+ + Tailwind CSS + Zustand for dashboard; TypeScript (Node.js 22 LTS or Bun) for CLI; PostgreSQL + Redis + ChromaDB for data; Turborepo monorepo; `uv` (Python) + `pnpm` (Node.js) package managers; `ruff` for Python linting; `mypy --strict` for type checking
- **Quality bar:** Production-grade — fully polished, tested, documented, open-source ready, installable by anyone
- **No deadline** — build it right

## Constraints

- **Tech stack**: Python 3.12+ backend, React/Vite dashboard, TypeScript CLI — as specified in PRD and CLAUDE.md
- **LLM providers (v1)**: Claude Code (SDK), OpenAI Codex (CLI), Google Gemini (CLI), Ollama, LM Studio
- **Mobile (v1)**: React Native only — no native iOS/Android or Flutter
- **Collaboration (v1)**: No real-time CRDT — agents work autonomously, humans review after
- **Monorepo**: Turborepo with `apps/` (server, dashboard, cli) and `libs/` (agent-sdk, shared-types, graph-engine)
- **Python standards**: `ruff format` + `ruff check`, `mypy --strict`, dataclasses with `slots=True`, `asyncio.TaskGroup` for concurrency
- **TypeScript standards**: strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`
- **Agent configs**: YAML-declarative in `configs/`
- **Pipeline presets**: `full.yaml`, `quick.yaml`, `review-only.yaml`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React Native for mobile (no native iOS/Android/Flutter) | Reduces mobile complexity while covering both platforms; aligns with web React skills | -- Pending |
| Defer CRDT real-time collaboration to v2 | High complexity, not core to autonomous pipeline value; agents work in isolated worktrees anyway | -- Pending |
| LLM scope: Claude Code + Codex + Gemini + Ollama + LM Studio | Covers cloud + self-hosted needs without over-engineering the provider abstraction layer | -- Pending |
| Full PRD scope for v1 (all 30 agents, all stages, all project modes) | User wants production-grade, complete platform | -- Pending |
| Deployment (S10) included in v1 | Full end-to-end pipeline is the core value proposition | -- Pending |

---
*Last updated: 2026-03-18 after initialization*
