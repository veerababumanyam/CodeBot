# Feature Research

**Domain:** Autonomous multi-agent SDLC platform (idea-to-production code generation)
**Researched:** 2026-03-18
**Confidence:** HIGH — Informed by PRD v2.5, RESEARCH_SUMMARY.md, competitive landscape analysis from existing docs, and analysis of comparable platforms (Devin, Bolt.new, Cursor, AutoGen, CrewAI, Codebuff, Automaker, Superset)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users of any autonomous code-generation platform assume exist. Missing these = product feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language input to working code | Core value proposition — if this fails, nothing else matters | HIGH | Must produce runnable, not just syntactically valid, code |
| Multi-file, multi-module code generation | Real projects span dozens of files; single-file generators aren't useful | HIGH | Requires cross-file context and coherent naming |
| Git integration (branch, commit, PR creation) | Every developer uses git; generated code without version control is a dead end | MEDIUM | Automated branch-per-feature + PR description generation |
| Automated test generation | Users won't trust generated code without tests | HIGH | Unit + integration tests at minimum; coverage gate enforcement |
| Dependency management (package.json, pyproject.toml, etc.) | Missing or broken deps = code that can't run | MEDIUM | Resolve versions, pin lockfiles, detect conflicts |
| Project scaffolding / boilerplate generation | Setting up folder structure, configs, CI files is expected automatically | MEDIUM | Language/framework-specific templates |
| Linting and formatting (ruff, biome, prettier) | Generated code must meet style standards; raw LLM output rarely does | MEDIUM | Auto-apply formatters as post-processing step |
| Error detection and auto-fix loop | LLMs produce bugs; a platform that can't fix its own errors is unusable | HIGH | Parse test/compiler output, generate targeted fixes, re-run |
| CLI interface | Developers expect headless operation for scripting and CI | MEDIUM | `init`, `run`, `status`, `deploy` subcommands at minimum |
| Progress visibility (what is the agent doing right now?) | Black-box generation creates anxiety; users abandon platforms that don't explain their actions | MEDIUM | Streaming log output or live status in CLI/dashboard |
| Multi-LLM provider support | No single model is best at everything; vendor lock-in is a red flag for serious users | HIGH | At minimum: Anthropic, OpenAI, Google — with unified interface |
| Human-in-the-loop approval gates | Fully autonomous pipelines that can't be paused or reviewed are unsafe for production use | MEDIUM | Configurable checkpoint system, not just hardcoded gates |
| Project context persistence across sessions | Users expect the system to remember what it built; starting fresh every session is a deal-breaker | HIGH | Project state storage with resumable pipeline |
| Sandbox / safe code execution | Running AI-generated code on the host machine without isolation is a critical safety gap | HIGH | Containerized execution per agent; network egress controls |
| README and basic documentation generation | Deliverables must be hand-offable; raw code without docs is incomplete | LOW | README, inline comments, API reference stubs |
| Support for popular frameworks | React, FastAPI, Next.js, Express — not supporting mainstream choices limits addressable market | HIGH | Framework-aware generation, not generic code dumps |
| Cost visibility (token usage, estimated spend) | LLM costs are a major concern; users need to see what they're spending | MEDIUM | Per-run token tracking, per-stage cost breakdown |
| Configurable pipeline presets | "Full pipeline" is expensive; users need quick/review-only modes | LOW | YAML-declarative presets: full, quick, review-only |
| Idempotent reruns / resume from checkpoint | Network failures, budget limits, or manual stops must not restart the entire pipeline | HIGH | Checkpoint-based state; replay from last successful stage |

---

### Differentiators (Competitive Advantage)

Features that distinguish CodeBot in the competitive field. These are where CodeBot wins — not everything, but the features that map to the core value proposition: "From Brainstorm to Production — Autonomously, Everywhere."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Graph-centric 30-agent SDLC pipeline (S0–S10) | No competitor covers the full lifecycle end-to-end; most stop at code generation | VERY HIGH | MASFactory-inspired DAG execution; parallel stages S3–S6, S8; LangGraph + Temporal backing |
| 4 project modes: greenfield, inflight, brownfield, improve | Competitors only handle new projects; brownfield and improve modes address the enormous legacy codebase market | HIGH | Codebase import + AST analysis for inflight/brownfield; improve mode runs optimization loop autonomously |
| Full security pipeline (SAST, DAST, SCA, secrets, license) | Security is an afterthought in most generators; integrated gates make CodeBot enterprise-credible | HIGH | Semgrep, Trivy, Gitleaks, ZAP, ORT — all wired into the pipeline, not optional add-ons |
| Comprehensive testing suite (13 test types) | Competitors generate unit tests at best; CodeBot generates and runs unit, integration, E2E, mutation, contract, performance, accessibility, visual regression, chaos | VERY HIGH | Playwright, Vitest, pytest, k6, axe-core, Pact, Stryker — differentiated by breadth and automation |
| Intelligent multi-LLM routing (task-aware, cost-aware, privacy-aware) | Route brainstorming to Claude, code generation to Codex, research to Gemini — per-task optimization, not per-project selection | HIGH | LiteLLM + RouteLLM; routing rules in YAML config |
| Self-hosted / air-gapped LLM support (Ollama, LM Studio, vLLM) | Enterprise and privacy-sensitive users cannot use cloud LLMs; this unlocks regulated industries | MEDIUM | Offline mode with full pipeline on local models; auto-detect running instances |
| Live application preview mid-pipeline | Users can interact with the app while it's still being built; no competitor does this | HIGH | Containerized hot-reload server proxied to dashboard; mobile viewport emulation; VNC for desktop apps |
| Git worktree isolation per coding agent | Prevents multi-agent file conflicts; enables true parallel implementation | MEDIUM | One worktree per agent; merge coordinator resolves conflicts post-implementation |
| Brainstorming phase with competitive analysis and scope definition | Most platforms start at PRD input; CodeBot starts at the raw idea and helps shape it | MEDIUM | Problem-solution mapping, feature prioritization via MoSCoW/RICE/Kano, market fit assessment |
| Automated cloud deployment to 8+ providers (AWS, GCP, Azure, Vercel, Railway, Fly.io, Netlify, DigitalOcean) | Full idea-to-deployed-URL in a single pipeline; no competitor automates this end-to-end | HIGH | IaC generation via Pulumi + OpenTofu; multi-environment management; rollback automation |
| iOS App Store and Google Play Store submission automation | Mobile app pipeline is effectively not covered by any competitor | VERY HIGH | Build, sign, TestFlight/internal testing upload, submission preparation |
| Multi-repo support with cross-repo dependency management | Modern microservice/polyrepo architectures require coordinated multi-repo builds; no competitor handles this | HIGH | Cross-repo dependency graphs; topological build ordering |
| 3-tier hierarchical context management (L0/L1/L2) with episodic memory | Token-efficient context loading; cross-session and cross-project learning makes the system improve over time | HIGH | L0 always-loaded, L1 on-demand, L2 deep retrieval; Chroma + SQLite episodic store |
| Self-improving agent ecosystem (skill, hook, tool creation) | Agents create reusable skills for other agents; the platform becomes more capable with each project | VERY HIGH | Anti-pattern registry, pattern library, cross-project learning; agents can generate new tools |
| WCAG 2.1 AA/AAA accessibility compliance built-in | Accessibility is legally required in many markets; most generators ignore it entirely | MEDIUM | axe-core, Lighthouse, pa11y wired into review and test phases |
| Internationalization (i18n/L10n) review and enforcement | Global products need i18n from the start; retrofitting is expensive | MEDIUM | Hardcoded string detection, locale support check, RTL layout verification |
| Architecture Decision Record (ADR) generation | Long-lived projects need rationale documentation; CodeBot generates ADRs automatically | LOW | Auto-generated from agent decision logs during design phase |
| Multi-modal input (images, voice, video, URLs, diagrams) | Accept wireframes, screenshots, voice recordings, and reference URLs — not just text | MEDIUM | Gemini's vision capabilities for image/video; Whisper for voice transcription |
| React Native mobile code generation | Web + mobile in one pipeline; competitors that do mobile at all handle only web views | HIGH | Shared component generation; platform-aware code paths |
| Plugin system (agent, tool, template, LLM provider plugins) | Extensibility lets enterprises customize CodeBot without forking it | HIGH | pluggy + setuptools entry_points; community plugin registry |
| Open source (Apache-2.0 or MIT) | No vendor lock-in; enterprise trust; community contributions | LOW | Architectural decision, not a feature to build — but a massive differentiator |
| Cost intelligence dashboard with per-agent token tracking | Users need to understand which agents are expensive and optimize accordingly | MEDIUM | Langfuse integration; per-stage cost breakdown; budget limit enforcement |
| Pipeline visualization (React Flow DAG) | Seeing the agent graph execute in real time builds trust and understanding | MEDIUM | React Flow + ELKjs; live node state, edge animation during execution |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem appealing but create more problems than value. Documenting these prevents scope creep and preserves architectural integrity.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time CRDT collaboration (humans + agents editing simultaneously) | Feels powerful — like Google Docs for code | Agents work in isolated git worktrees; CRDT for code conflicts with the worktree isolation model, adds massive complexity (Yjs + operational transform), and conflicts with autonomous pipeline flow | Human-in-the-loop approval gates at phase boundaries; humans review diffs, not edit alongside agents |
| Always-on fully autonomous self-improvement (no human gate) | Maximum automation appeal | Autonomous agents modifying their own skills and tools without review is a safety/trust risk; hallucinated "improvements" can corrupt the skill library | Skill creation with human review before activation; pattern library grows incrementally with validation |
| "Generate everything from one line" UX promise | Marketing appeal | Single-line inputs produce underspecified outputs that require massive clarification loops, damaging trust more than a structured input step | Structured brainstorming phase that gathers context before pipeline runs; PRD ingestion for structured input |
| Per-file streaming output to the user | Feels responsive | Files generated mid-pipeline are incomplete and often wrong before cross-file reconciliation; showing them creates confusion about what's final | Stream agent status/logs, not partial file contents; show preview only when the stage is complete |
| Support every LLM provider from day one | Comprehensive appeal | Each provider has different tool call formats, context windows, and capability profiles; supporting 20+ providers before validating routing logic wastes significant effort | Start with 5 validated providers (Claude, OpenAI, Gemini, Ollama, LM Studio) with provider-agnostic LiteLLM layer; add providers via community plugins |
| Native iOS (Swift/SwiftUI) + native Android (Kotlin/Compose) + Flutter simultaneously | Broadest platform coverage | Each native platform requires deeply specialized agents with distinct tool chains, APIs, and review criteria; building all three doubles mobile complexity without proportional value | React Native for v1 (covers both iOS and Android with one codebase); native platforms deferred to v2 |
| Monolithic agent (one super-agent does everything) | Simplicity | Context window limits mean a single agent cannot hold the full SDLC context; specialization allows each agent to be optimized for its domain with appropriate tools and prompts | 30 specialized agents with domain-specific context, tools, and system prompts; graph orchestration manages dependencies |
| In-browser code editor as primary interface | Familiar UX | A browser editor encourages treating CodeBot as an IDE rather than an autonomous pipeline; it blurs the human/agent boundary and creates expectations of manual editing | Monaco editor in dashboard for review and targeted edits only; primary workflow is pipeline-driven, not editor-driven |
| Instant deployment with no configuration | Zero-friction appeal | Deployment without configuration produces deployments users can't control, debug, or reproduce; no custom domains, secrets management, or environment separation | Opt-in deployment (S10) with explicit configuration step; deploy-anywhere with IaC artifacts as first-class outputs |
| Built-in LLM (run a model inside CodeBot) | Self-contained appeal | Running a capable LLM inside the platform requires enormous GPU resources; it competes with the multi-LLM routing advantage | First-class Ollama and LM Studio support for local model execution outside CodeBot; CodeBot orchestrates, not hosts |
| Chat-first interface as the only UX | Low barrier to entry | Chat is good for exploration but poor for structured pipeline control; it obscures pipeline state, cost, and progress | Chat is one input mode in brainstorming; structured dashboard + CLI are primary interfaces for pipeline management |

---

## Feature Dependencies

```
Natural Language Input
    └──enables──> Brainstorming Phase (S1)
                      └──requires──> Project Context Persistence
                      └──enables──> Research Phase (S2)
                                        └──enables──> Architecture & Design Phase (S3)
                                                          └──enables──> Planning Phase (S4)
                                                                            └──enables──> Implementation Phase (S5)

Multi-LLM Routing
    └──requires──> LiteLLM Gateway
    └──requires──> Model Registry (per-provider capability metadata)
    └──enhances──> All pipeline stages (route each stage to best model)

3-Tier Context Management (L0/L1/L2)
    └──requires──> Vector Store (LanceDB / Qdrant)
    └──requires──> Tree-sitter Code Indexing
    └──enables──> Implementation Phase (agents need context to generate coherent code)
    └──enables──> Episodic Memory (L2 retrieval is the episodic layer)

Git Worktree Isolation
    └──requires──> Git Integration
    └──enables──> Parallel Implementation (S5 parallel agents)
    └──requires──> Merge Coordinator Agent (resolves post-implementation conflicts)

Sandbox Execution
    └──requires──> Docker / Container Runtime
    └──enables──> Live Preview
    └──enables──> Test Execution (tests run inside sandbox)
    └──enables──> Security DAST (app must run to be dynamically tested)

Security Pipeline (SAST, DAST, SCA, secrets)
    └──requires──> Sandbox Execution (for DAST)
    └──requires──> Git Integration (for secret scanning pre-commit hooks)
    └──runs-after──> Implementation Phase (S5)
    └──gates──> Testing Phase (S7) — security failures block progression

Automated Test Generation
    └──requires──> Code Generation (can't test what doesn't exist)
    └──requires──> Sandbox Execution (tests must run somewhere)
    └──gates──> Debug & Fix Cycle (S8) — test failures trigger fix loop

Debug & Fix Cycle (S8)
    └──requires──> Automated Test Generation
    └──requires──> Failure Analysis (parse test/compiler output)
    └──loops-until──> All tests pass OR human escalation

Cloud Deployment (S10)
    └──requires──> CI/CD Pipeline Generation
    └──requires──> IaC Generation (Pulumi / OpenTofu)
    └──requires──> Sandbox Execution (build artifacts run in containers)
    └──requires──> All upstream stages complete (S0–S9)

Episodic Memory / Cross-project Learning
    └──requires──> 3-Tier Context Management
    └──requires──> Vector Store
    └──enhances──> All agents (past observations improve future decisions)

Self-improving Agent Ecosystem (skill/hook/tool creation)
    └──requires──> Episodic Memory
    └──requires──> Pattern Library store
    └──requires──> Human approval gate (skills reviewed before activation)
    └──enhances──> Implementation Phase (reuse reduces token cost and errors)

Plugin System
    └──requires──> Stable internal agent API (cannot build plugins before core agent interface is stable)
    └──enables──> Community LLM providers, custom agents, custom templates

Mobile (React Native) Generation
    └──requires──> Implementation Phase (S5) infrastructure
    └──requires──> Shared component generation
    └──enhances──> Cross-platform deployment (iOS App Store + Google Play)
```

### Dependency Notes

- **Context management requires vector store:** L2 retrieval is semantic search over code embeddings; without a vector store, only L0/L1 (in-memory and file-based) tiers work, which is insufficient for large codebases.
- **DAST requires sandbox execution:** Dynamic application security testing (OWASP ZAP) needs a running application; this means sandbox execution must be stable before the full security pipeline can run.
- **Self-improving ecosystem requires episodic memory:** Agents cannot create useful skills without access to cross-session observation history to identify recurring patterns.
- **Plugin system requires stable agent API:** Building the plugin interface before the core agent API stabilizes risks breaking all plugins on every internal refactor. Plugin system belongs in v1.x, not v1.0.
- **Cloud deployment (S10) depends on everything upstream:** A deployment failure caused by a code defect that wasn't caught in testing damages trust more than not deploying at all. All gates must pass before S10 runs.
- **Parallel implementation requires git worktree isolation:** Without isolated worktrees, concurrent agents overwrite each other's changes. These two features are inseparable.

---

## MVP Definition

The project's stated goal is a production-grade, complete platform with all 30 agents and all 11 stages. The following classification reflects what must work correctly for the platform to be credible at first public release vs. what can be hardened or expanded after initial validation.

### Launch With (v1.0)

Minimum required for CodeBot to be a credible autonomous development platform:

- [ ] **Graph engine + pipeline execution** (LangGraph + Temporal) — the foundation; nothing else works without it
- [ ] **Natural language / PRD input processing** — the entry point; must handle structured and free-form input
- [ ] **Brainstorming phase (S1)** — differentiates from competitors that start at PRD
- [ ] **Research phase (S2)** — required to inform architecture decisions
- [ ] **Architecture + planning phases (S3–S4)** — without these, code generation is unstructured
- [ ] **Implementation phase (S5)** with git worktree isolation — the core code generation stage; must work for at minimum Python/FastAPI backend + React/TypeScript frontend
- [ ] **3-tier context management (L0/L1/L2)** — required for coherent multi-file generation
- [ ] **Multi-LLM routing** (Claude, OpenAI, Gemini, Ollama, LM Studio) — table stakes for the product's LLM strategy
- [ ] **Sandbox execution per agent** — required for safe code execution and testing
- [ ] **Automated test generation and execution** (unit + integration at minimum) — required to establish trust
- [ ] **Debug & fix cycle (S8)** — required; generated code always has bugs on first pass
- [ ] **SAST security scanning** (Semgrep + Gitleaks minimum) — minimum credible security gate
- [ ] **Documentation generation (S9)** — README, API docs, ADRs
- [ ] **CLI interface** — required for headless operation and scripting
- [ ] **Web dashboard** — pipeline visualization, agent activity, progress, cost tracking
- [ ] **Human-in-the-loop approval gates** — required for trust; users must be able to pause and review
- [ ] **Cost tracking** (token usage per agent/stage, budget limits) — required to prevent runaway costs
- [ ] **Checkpoint-based pipeline resume** — required; long pipelines will fail midway

### Add After Validation (v1.x)

Features to add once core pipeline is proven:

- [ ] **Full security pipeline** (DAST + SCA + license compliance) — add when sandbox execution is stable; DAST depends on running app
- [ ] **Full test suite** (E2E Playwright, performance k6, accessibility axe-core, visual regression, contract Pact, mutation Stryker) — expand test coverage after unit/integration are working
- [ ] **React Native mobile generation** — add after web pipeline is stable; same agent infrastructure, new framework templates
- [ ] **Cloud deployment (S10)** — add after pipeline produces high-quality code that passes all gates; shipping broken code to production is worse than not shipping
- [ ] **Episodic memory / cross-session learning** — add when sufficient project data exists to train the pattern library
- [ ] **Plugin system** — add when internal agent API is stable; premature plugins create compatibility debt
- [ ] **Brownfield / inflight project modes** — complex codebase import and analysis; add after greenfield is proven
- [ ] **IDE extensions** (VS Code, JetBrains, Cursor) — surface integrations; add when core platform is stable
- [ ] **Multi-modal input** (images, voice, video) — useful but not blocking for text-first launch
- [ ] **Multi-repo support** — complex coordination; add when single-repo is production-grade

### Future Consideration (v2+)

Features to defer until product-market fit is established:

- [ ] **Real-time CRDT collaboration** — very high complexity; conflicts with worktree isolation model; defer until collaboration use cases are validated
- [ ] **Self-improving agent ecosystem** (autonomous skill/tool creation) — requires extensive episodic memory data and careful safety review workflow; defer until memory system matures
- [ ] **Native iOS + Android** (Swift + Kotlin) — React Native covers v1 mobile; native requires entirely new specialized agents
- [ ] **Autonomous improve mode** (continuous optimization without human trigger) — requires proven pipeline quality and safety guardrails
- [ ] **App Store / Play Store submission automation** — depends on stable mobile pipeline and Apple/Google API stability
- [ ] **SaaS / hosted version** — infrastructure, billing, multi-tenancy; defer until self-hosted version is proven

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Graph engine + pipeline execution | HIGH | HIGH | P1 |
| Natural language / PRD input | HIGH | MEDIUM | P1 |
| Multi-LLM routing (5 providers) | HIGH | HIGH | P1 |
| Implementation phase (S5) code generation | HIGH | HIGH | P1 |
| 3-tier context management | HIGH | HIGH | P1 |
| Git integration + worktree isolation | HIGH | MEDIUM | P1 |
| Sandbox execution per agent | HIGH | HIGH | P1 |
| Automated test generation (unit + integration) | HIGH | HIGH | P1 |
| Debug & fix cycle (S8) | HIGH | HIGH | P1 |
| CLI interface | HIGH | MEDIUM | P1 |
| Web dashboard (pipeline + agent view) | HIGH | HIGH | P1 |
| Human-in-the-loop approval gates | HIGH | MEDIUM | P1 |
| Cost tracking (token/stage/budget) | HIGH | MEDIUM | P1 |
| Checkpoint-based pipeline resume | HIGH | MEDIUM | P1 |
| Brainstorming phase (S1) | MEDIUM | MEDIUM | P1 |
| Research phase (S2) | MEDIUM | MEDIUM | P1 |
| Architecture + planning phases (S3–S4) | HIGH | HIGH | P1 |
| SAST security scanning (Semgrep, Gitleaks) | HIGH | LOW | P1 |
| Documentation generation (S9) | MEDIUM | LOW | P1 |
| Full security pipeline (DAST, SCA, license) | HIGH | HIGH | P2 |
| Full test suite (E2E, perf, a11y, mutation) | HIGH | VERY HIGH | P2 |
| React Native mobile generation | HIGH | HIGH | P2 |
| Cloud deployment (S10) | HIGH | VERY HIGH | P2 |
| Episodic memory / cross-session learning | MEDIUM | HIGH | P2 |
| Brownfield / inflight modes | HIGH | HIGH | P2 |
| Multi-modal input | MEDIUM | MEDIUM | P2 |
| Multi-repo support | MEDIUM | HIGH | P2 |
| IDE extensions | MEDIUM | MEDIUM | P2 |
| Plugin system | MEDIUM | HIGH | P2 |
| Self-improving agent ecosystem | HIGH | VERY HIGH | P3 |
| Real-time CRDT collaboration | MEDIUM | VERY HIGH | P3 |
| Native iOS + Android | HIGH | VERY HIGH | P3 |
| Autonomous improve mode | HIGH | VERY HIGH | P3 |
| App Store / Play Store automation | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

Sources: CodeBot RESEARCH_SUMMARY.md, PRD competitive landscape section, public documentation of listed products.

| Feature | Devin (Cognition) | Bolt.new / Lovable | Cursor / Windsurf | Cline / Roo Code | AutoGen / CrewAI | CodeBot |
|---------|-------------------|--------------------|-------------------|------------------|------------------|---------|
| Full SDLC pipeline (brainstorm → deploy) | Partial (implement → debug) | Partial (scaffold → preview) | No (editor-only) | No (implement → debug) | No (framework only) | Yes — S0 through S10 |
| Multi-LLM routing (task-aware) | No (proprietary model) | No (locked LLM) | Partial (model select) | Partial (model select) | Yes (model config) | Yes — 5+ providers, per-task routing |
| Self-hosted / air-gapped LLM | No | No | No | Partial (Ollama) | Yes | Yes — Ollama, LM Studio, vLLM |
| Security pipeline (SAST, DAST, SCA) | No | No | No | No | No | Yes — integrated gates |
| 13-type automated testing | No (unit only) | No | No | No | No | Yes |
| Mobile generation (React Native) | No | No | No | No | No | Yes |
| Cloud deployment automation | No | Partial (Netlify) | No | No | No | Yes — 8+ providers |
| Git worktree isolation (parallel agents) | No | No | No | No | No | Yes |
| Brownfield / legacy codebase support | Partial | No | Partial (existing code) | Partial | No | Yes — dedicated mode |
| Human-in-the-loop gates | Partial | No | Yes (user-driven) | Yes (user-driven) | Yes | Yes — configurable checkpoints |
| Context management (hierarchical, L0/L1/L2) | Unknown | No | Partial | Partial | No | Yes — 3-tier native system |
| Cross-project episodic memory | No | No | No | No | No | Yes |
| Accessibility (WCAG) enforcement | No | No | No | No | No | Yes — built-in review + test |
| Open source | No (proprietary) | No | Partial (Cline) | Yes (Cline) | Yes | Yes |
| Plugin / extension system | No | No | Yes (VS Code) | Yes (VS Code) | Yes | Yes — pluggy-based |
| Cost per-agent tracking | No | No | No | No | No | Yes — Langfuse integration |

---

## Sources

- CodeBot PRD v2.5 (`docs/prd/PRD.md`) — feature definitions for all 11 pipeline stages
- CodeBot RESEARCH_SUMMARY.md (`docs/refernces/RESEARCH_SUMMARY.md`) — competitive landscape, technology evaluations
- CodeBot PROJECT.md (`.planning/PROJECT.md`) — requirements, constraints, key decisions
- MASFactory (arXiv:2603.06007) — multi-agent pipeline patterns, graph execution model
- Competitive products analyzed: Devin (Cognition), GitHub Copilot Workspace, Cursor, Windsurf, Bolt.new, Lovable, Cline, Roo Code, AutoGen, CrewAI, Automaker, Codebuff, Superset
- Referenced open-source projects: LangGraph, Temporal, LiteLLM, RouteLLM, FastMCP, LanceDB, Qdrant, Tree-sitter, Playwright, axe-core, Semgrep, Trivy, OpenTelemetry, Langfuse

---

*Feature research for: Autonomous multi-agent SDLC platform*
*Researched: 2026-03-18*
