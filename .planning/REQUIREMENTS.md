# Requirements: CodeBot

**Defined:** 2026-03-18
**Core Value:** A user can describe an idea and get working, tested, security-scanned code autonomously through a multi-agent pipeline

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Graph Engine

- [x] **GRPH-01**: System can execute directed graphs with typed nodes and edges in topological order
- [x] **GRPH-02**: System supports node types: AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM
- [x] **GRPH-03**: System provides SharedState for graph-level data flow between nodes
- [x] **GRPH-04**: System can load and validate graph definitions from YAML
- [x] **GRPH-05**: System detects cycles, missing dependencies, and invalid edge types during validation
- [x] **GRPH-06**: System can checkpoint graph state and resume execution from checkpoint
- [x] **GRPH-07**: System traces execution with timing, token usage, and output per node
- [x] **GRPH-08**: System executes parallel branches concurrently via asyncio TaskGroup
- [x] **GRPH-09**: System supports conditional routing (SWITCH nodes) based on SharedState
- [x] **GRPH-10**: System supports dynamic fan-out via LangGraph Send API for parallel agent dispatch

### Agent Framework

- [x] **AGNT-01**: All agents extend BaseAgent with Perception-Reasoning-Action (PRA) cognitive cycle
- [x] **AGNT-02**: AgentNode wraps BaseAgent instances for graph execution with typed inputs/outputs
- [x] **AGNT-03**: Agents follow state machine: IDLE → INITIALIZING → EXECUTING → REVIEWING → COMPLETED/FAILED → RECOVERING
- [x] **AGNT-04**: Each coding agent operates in an isolated git worktree
- [x] **AGNT-05**: Agent configurations are declarative YAML (system prompt, tools, LLM model, context tiers, retry policy)
- [x] **AGNT-06**: Agents self-review output against acceptance criteria before marking COMPLETED
- [x] **AGNT-07**: Failed agents trigger recovery strategy (retry with different prompt, escalate, rollback)
- [ ] **AGNT-08**: System supports 30 specialized agents across 10 categories
- [ ] **AGNT-09**: Skill Creator agent can generate reusable skills for other agents
- [ ] **AGNT-10**: Hooks Creator agent can create event-triggered hooks
- [ ] **AGNT-11**: Tools Creator agent can expose new tool capabilities to the agent ecosystem
- [x] **AGNT-12**: Agent metrics tracked: execution time, token usage, cost, success rate, retry count

### Multi-LLM Abstraction

- [x] **LLM-01**: System provides provider-agnostic interface via LiteLLM supporting Anthropic, OpenAI, Google, and self-hosted (Ollama/vLLM)
- [x] **LLM-02**: System routes tasks to optimal model by task type, complexity, privacy, cost, and latency via RouteLLM
- [x] **LLM-03**: System supports fallback chains (primary model fails → fallback model)
- [x] **LLM-04**: System tracks token usage and cost per agent, per stage, per model
- [x] **LLM-05**: System supports streaming responses for real-time output
- [x] **LLM-06**: System can operate fully air-gapped with self-hosted models only
- [x] **LLM-07**: Cost estimates provided before pipeline execution begins
- [x] **LLM-08**: Budget limits can halt execution when cost threshold exceeded

### Pipeline Orchestration

- [ ] **PIPE-01**: System executes 10-stage SDLC pipeline: S0 Init → S1 Brainstorm → S2 Research → S3 Architecture → S4 Planning → S5 Implementation → S6 QA → S7 Testing → S8 Debug → S9 Documentation
- [ ] **PIPE-02**: Stages S3, S5, and S6 execute agents in parallel via DAG topology
- [x] **PIPE-03**: Pipeline supports entry/exit gates with human approval at configurable checkpoints
- [x] **PIPE-04**: Pipeline configurations loadable from YAML presets: full, quick, review-only
- [x] **PIPE-05**: Temporal provides durable workflow orchestration with retry, timeout, and crash recovery
- [ ] **PIPE-06**: Pipeline can resume from last checkpoint after failure or manual pause
- [x] **PIPE-07**: Pipeline detects project type (greenfield, inflight, brownfield) and adapts stage configuration
- [x] **PIPE-08**: Pipeline emits events to NATS JetStream for every stage transition, agent action, and gate decision

### Input Processing (S0)

- [ ] **INPT-01**: User can describe project idea in natural language
- [ ] **INPT-02**: System accepts structured PRDs in Markdown, JSON, or YAML
- [ ] **INPT-03**: System accepts multi-modal input: text, images (wireframes, screenshots), and reference URLs
- [ ] **INPT-04**: System extracts functional requirements, non-functional requirements, constraints, and acceptance criteria via NLP
- [ ] **INPT-05**: System initiates clarification loop when requirements are ambiguous or incomplete
- [ ] **INPT-06**: User can select UI/UX template (Shadcn/ui, Tailwind UI, Material Design, custom)
- [ ] **INPT-07**: User can select or auto-recommend tech stack (language, framework, database, hosting)
- [ ] **INPT-08**: System imports existing codebases from local directories or Git repositories for brownfield projects

### Brainstorming (S1)

- [ ] **BRST-01**: System facilitates idea exploration sessions with open-ended brainstorming
- [ ] **BRST-02**: System maps problems to potential solution approaches
- [ ] **BRST-03**: System performs competitive analysis of existing solutions
- [ ] **BRST-04**: System prioritizes features using MoSCoW or RICE frameworks
- [ ] **BRST-05**: System presents trade-off analysis for architectural and feature decisions
- [ ] **BRST-06**: System generates user personas based on product idea
- [ ] **BRST-07**: System defines MVP scope vs future iterations

### Research (S2)

- [ ] **RSRC-01**: Researcher agent evaluates libraries, APIs, and frameworks for the target stack
- [ ] **RSRC-02**: Researcher discovers best practices and reference implementations
- [ ] **RSRC-03**: Researcher identifies potential risks and compatibility issues
- [ ] **RSRC-04**: Research outputs feed into Architecture phase as structured context

### Architecture & Design (S3)

- [ ] **ARCH-01**: Architect agent designs system architecture with component boundaries and data flow
- [ ] **ARCH-02**: API Designer agent generates REST/GraphQL API specifications
- [ ] **ARCH-03**: Database Designer agent creates schema with migrations
- [ ] **ARCH-04**: UI/UX Designer agent generates wireframes and component hierarchy
- [ ] **ARCH-05**: S3 agents execute in parallel with SharedState for cross-agent data flow
- [ ] **ARCH-06**: Architecture outputs validated against requirements before advancing

### Planning (S4)

- [ ] **PLAN-01**: Planner agent decomposes architecture into implementable tasks with dependencies
- [ ] **PLAN-02**: Task dependency graph determines execution order and parallelization opportunities
- [ ] **PLAN-03**: Each task specifies target files, acceptance criteria, and estimated complexity

### Implementation (S5)

- [ ] **IMPL-01**: Frontend agent generates React/TypeScript UI code from design specs
- [ ] **IMPL-02**: Backend agent generates Python/FastAPI server code from API specs
- [ ] **IMPL-03**: Mobile agent generates cross-platform or native mobile code
- [ ] **IMPL-04**: Infrastructure agent generates Docker, CI/CD, and config files
- [ ] **IMPL-05**: S5 agents execute in parallel in isolated git worktrees
- [ ] **IMPL-06**: CLI agent integration delegates coding to Claude Code, Codex CLI, or Gemini CLI
- [ ] **IMPL-07**: Generated code follows project style conventions and linting rules

### Quality Assurance (S6)

- [ ] **QA-01**: Code Review agent reviews generated code for correctness, patterns, and maintainability
- [ ] **QA-02**: Security Scanner agent runs Semgrep, Trivy, and Gitleaks on all generated code
- [ ] **QA-03**: Accessibility agent audits UI for WCAG 2.1 AA compliance
- [ ] **QA-04**: Performance agent profiles code for bottlenecks and optimization opportunities
- [ ] **QA-05**: i18n/L10n agent verifies internationalization completeness
- [ ] **QA-06**: Quality gates must pass before code advances to Testing phase
- [ ] **QA-07**: S6 agents execute in parallel

### Testing (S7)

- [ ] **TEST-01**: Test Generator agent creates unit tests with >= 80% line coverage target
- [ ] **TEST-02**: Test Generator creates integration tests for API endpoints and data flows
- [ ] **TEST-03**: Test Generator creates E2E tests using Playwright/Vitest
- [ ] **TEST-04**: Tests execute in sandboxed environments (Docker containers)
- [ ] **TEST-05**: Test results feed back to Debug phase when failures detected

### Debug & Fix (S8)

- [ ] **DBUG-01**: Debugger agent performs root cause analysis on test failures
- [ ] **DBUG-02**: Debugger generates fix proposals and applies them
- [ ] **DBUG-03**: Fix-test loop iterates until all tests pass or max retries exceeded
- [ ] **DBUG-04**: Security-specific debugging addresses vulnerability findings from S6

### Documentation (S9)

- [ ] **DOCS-01**: Documentation agent generates API documentation from code
- [ ] **DOCS-02**: Documentation agent creates user guides and setup instructions
- [ ] **DOCS-03**: Documentation agent produces architecture decision records
- [ ] **DOCS-04**: Generated docs include deployment guides (Docker, CI/CD configs)

### Context Management

- [x] **CTXT-01**: L0 context (always present): project config, current task, agent system prompt
- [x] **CTXT-02**: L1 context (phase-scoped): phase requirements, related code files, architecture decisions
- [x] **CTXT-03**: L2 context (on-demand): vector store retrieval for code search, documentation lookup
- [x] **CTXT-04**: Vector store (LanceDB/Qdrant) indexes codebase for semantic search
- [x] **CTXT-05**: Tree-sitter parses code for structural understanding (functions, classes, imports)
- [x] **CTXT-06**: Context compression summarizes large outputs to fit within token budgets
- [x] **CTXT-07**: Hard token budgets enforced per agent call to prevent context exhaustion

### Security Pipeline

- [ ] **SECP-01**: Semgrep runs static analysis with custom rules for AI-generated code patterns
- [ ] **SECP-02**: Trivy scans container images and dependencies for known vulnerabilities
- [ ] **SECP-03**: Gitleaks detects secrets, API keys, and credentials in generated code
- [ ] **SECP-04**: Quality gates block advancement when critical/high vulnerabilities found
- [ ] **SECP-05**: Security scanning runs after every code generation step, not just at S6 gate
- [ ] **SECP-06**: Dependency allowlist prevents hallucinated/malicious package installation

### FastAPI Server

- [ ] **SRVR-01**: REST API endpoints for project CRUD, pipeline control, and agent monitoring
- [ ] **SRVR-02**: WebSocket endpoint for real-time pipeline status and agent output streaming
- [ ] **SRVR-03**: Authentication and authorization for API access
- [ ] **SRVR-04**: Pipeline configuration endpoints accept YAML preset selection
- [ ] **SRVR-05**: Agent management endpoints (start, stop, restart, configure)

### React Dashboard

- [ ] **DASH-01**: Real-time pipeline visualization using React Flow with node status indicators
- [ ] **DASH-02**: Agent monitoring panel showing status, logs, and metrics per agent
- [ ] **DASH-03**: Code editor integration via Monaco Editor for viewing/editing generated code
- [ ] **DASH-04**: Terminal emulator via xterm.js for CLI interaction within dashboard
- [ ] **DASH-05**: CRDT-based real-time collaboration via Yjs for human-AI co-editing
- [ ] **DASH-06**: Socket.IO live updates for pipeline progress and agent events
- [ ] **DASH-07**: Cost dashboard showing token usage and cost breakdown per agent/stage/model
- [ ] **DASH-08**: Live preview panel showing running application mid-pipeline via sandbox hot-reload

### CLI Application

- [ ] **CLI-01**: TypeScript CLI for project creation with interactive prompts
- [ ] **CLI-02**: Pipeline execution commands (start, pause, resume, stop)
- [ ] **CLI-03**: Agent status and log streaming from terminal
- [ ] **CLI-04**: Pipeline preset selection (full, quick, review-only)

### Event System

- [ ] **EVNT-01**: NATS JetStream pub/sub for all inter-agent messaging
- [ ] **EVNT-02**: Event replay capability for debugging and audit
- [ ] **EVNT-03**: Full audit trail: every agent action, gate decision, and state transition persisted
- [ ] **EVNT-04**: Event-sourced architecture enables complete pipeline reconstruction from events

### Worktree Management

- [ ] **WORK-01**: Worktree lifecycle manager creates/cleans git worktrees per coding agent
- [ ] **WORK-02**: Per-worktree Docker Compose profiles for runtime isolation
- [ ] **WORK-03**: Dynamic port allocation prevents conflicts between parallel agents
- [ ] **WORK-04**: Sequential merge strategy with conflict detection for worktree results

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Deployment Automation (S10)

- **DPLY-01**: Automated cloud deployment to AWS, GCP, Azure
- **DPLY-02**: Terraform/Pulumi infrastructure-as-code generation
- **DPLY-03**: Kubernetes manifest generation and deployment
- **DPLY-04**: CI/CD pipeline generation (GitHub Actions, GitLab CI)

### Multi-Repository

- **MREP-01**: Cross-repo dependency management
- **MREP-02**: Multi-repo pipeline orchestration
- **MREP-03**: Cross-repo versioning and deployment ordering

### Platform Extensions

- **PEXT-01**: Plugin/extension marketplace
- **PEXT-02**: IDE extensions (VS Code, JetBrains)
- **PEXT-03**: Team features (multi-user, RBAC)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Custom LLM fine-tuning | RAG with vector store achieves similar results at lower cost; provider model improvements outpace custom fine-tuning |
| Every programming language from day one | Launch with Python, TypeScript/JavaScript, React; add languages incrementally based on demand |
| GUI-only interface (no CLI) | CLI-first for developer audience; dashboard enhances but does not replace CLI |
| Full autonomy without human gates | 48% of AI code is insecure; configurable autonomy with approval gates at phase boundaries |
| Built-in IDE / code editor | Monaco in dashboard for viewing; users keep their preferred IDE; integrate via MCP/LSP |
| S10 Cloud Deployment | Generate deployment configs/docs in S9; automated deployment deferred to v2 |
| Mobile dashboard app | Web dashboard sufficient for v1 |
| Billing/payment system | Open-source, no monetization in v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRPH-01 | Phase 2 | Complete |
| GRPH-02 | Phase 2 | Complete |
| GRPH-03 | Phase 2 | Complete |
| GRPH-04 | Phase 2 | Complete |
| GRPH-05 | Phase 2 | Complete |
| GRPH-06 | Phase 2 | Complete |
| GRPH-07 | Phase 2 | Complete |
| GRPH-08 | Phase 2 | Complete |
| GRPH-09 | Phase 2 | Complete |
| GRPH-10 | Phase 2 | Complete |
| AGNT-01 | Phase 3 | Complete |
| AGNT-02 | Phase 3 | Complete |
| AGNT-03 | Phase 3 | Complete |
| AGNT-04 | Phase 3 | Complete |
| AGNT-05 | Phase 3 | Complete |
| AGNT-06 | Phase 3 | Complete |
| AGNT-07 | Phase 3 | Complete |
| AGNT-08 | Phase 9 | Pending |
| AGNT-09 | Phase 11 | Pending |
| AGNT-10 | Phase 11 | Pending |
| AGNT-11 | Phase 11 | Pending |
| AGNT-12 | Phase 3 | Complete |
| LLM-01 | Phase 4 | Complete |
| LLM-02 | Phase 4 | Complete |
| LLM-03 | Phase 4 | Complete |
| LLM-04 | Phase 4 | Complete |
| LLM-05 | Phase 4 | Complete |
| LLM-06 | Phase 4 | Complete |
| LLM-07 | Phase 4 | Complete |
| LLM-08 | Phase 4 | Complete |
| PIPE-01 | Phase 6 | Pending |
| PIPE-02 | Phase 6 | Pending |
| PIPE-03 | Phase 6 | Complete |
| PIPE-04 | Phase 6 | Complete |
| PIPE-05 | Phase 6 | Complete |
| PIPE-06 | Phase 6 | Pending |
| PIPE-07 | Phase 6 | Complete |
| PIPE-08 | Phase 6 | Complete |
| INPT-01 | Phase 7 | Pending |
| INPT-02 | Phase 7 | Pending |
| INPT-03 | Phase 9 | Pending |
| INPT-04 | Phase 7 | Pending |
| INPT-05 | Phase 7 | Pending |
| INPT-06 | Phase 9 | Pending |
| INPT-07 | Phase 9 | Pending |
| INPT-08 | Phase 9 | Pending |
| BRST-01 | Phase 9 | Pending |
| BRST-02 | Phase 9 | Pending |
| BRST-03 | Phase 9 | Pending |
| BRST-04 | Phase 9 | Pending |
| BRST-05 | Phase 9 | Pending |
| BRST-06 | Phase 9 | Pending |
| BRST-07 | Phase 9 | Pending |
| RSRC-01 | Phase 9 | Pending |
| RSRC-02 | Phase 9 | Pending |
| RSRC-03 | Phase 9 | Pending |
| RSRC-04 | Phase 9 | Pending |
| ARCH-01 | Phase 9 | Pending |
| ARCH-02 | Phase 9 | Pending |
| ARCH-03 | Phase 9 | Pending |
| ARCH-04 | Phase 9 | Pending |
| ARCH-05 | Phase 9 | Pending |
| ARCH-06 | Phase 9 | Pending |
| PLAN-01 | Phase 9 | Pending |
| PLAN-02 | Phase 9 | Pending |
| PLAN-03 | Phase 9 | Pending |
| IMPL-01 | Phase 9 | Pending |
| IMPL-02 | Phase 7 | Pending |
| IMPL-03 | Phase 9 | Pending |
| IMPL-04 | Phase 9 | Pending |
| IMPL-05 | Phase 8 | Pending |
| IMPL-06 | Phase 8 | Pending |
| IMPL-07 | Phase 7 | Pending |
| QA-01 | Phase 7 | Pending |
| QA-02 | Phase 9 | Pending |
| QA-03 | Phase 9 | Pending |
| QA-04 | Phase 9 | Pending |
| QA-05 | Phase 9 | Pending |
| QA-06 | Phase 7 | Pending |
| QA-07 | Phase 9 | Pending |
| TEST-01 | Phase 7 | Pending |
| TEST-02 | Phase 7 | Pending |
| TEST-03 | Phase 9 | Pending |
| TEST-04 | Phase 9 | Pending |
| TEST-05 | Phase 7 | Pending |
| DBUG-01 | Phase 7 | Pending |
| DBUG-02 | Phase 7 | Pending |
| DBUG-03 | Phase 7 | Pending |
| DBUG-04 | Phase 9 | Pending |
| DOCS-01 | Phase 9 | Pending |
| DOCS-02 | Phase 9 | Pending |
| DOCS-03 | Phase 9 | Pending |
| DOCS-04 | Phase 9 | Pending |
| CTXT-01 | Phase 5 | Complete |
| CTXT-02 | Phase 5 | Complete |
| CTXT-03 | Phase 5 | Complete |
| CTXT-04 | Phase 5 | Complete |
| CTXT-05 | Phase 5 | Complete |
| CTXT-06 | Phase 5 | Complete |
| CTXT-07 | Phase 5 | Complete |
| SECP-01 | Phase 8 | Pending |
| SECP-02 | Phase 8 | Pending |
| SECP-03 | Phase 8 | Pending |
| SECP-04 | Phase 8 | Pending |
| SECP-05 | Phase 8 | Pending |
| SECP-06 | Phase 8 | Pending |
| SRVR-01 | Phase 10 | Pending |
| SRVR-02 | Phase 10 | Pending |
| SRVR-03 | Phase 10 | Pending |
| SRVR-04 | Phase 10 | Pending |
| SRVR-05 | Phase 10 | Pending |
| DASH-01 | Phase 11 | Pending |
| DASH-02 | Phase 11 | Pending |
| DASH-03 | Phase 11 | Pending |
| DASH-04 | Phase 11 | Pending |
| DASH-05 | Phase 11 | Pending |
| DASH-06 | Phase 11 | Pending |
| DASH-07 | Phase 11 | Pending |
| DASH-08 | Phase 11 | Pending |
| CLI-01 | Phase 11 | Pending |
| CLI-02 | Phase 11 | Pending |
| CLI-03 | Phase 11 | Pending |
| CLI-04 | Phase 11 | Pending |
| EVNT-01 | Phase 7 | Pending |
| EVNT-02 | Phase 9 | Pending |
| EVNT-03 | Phase 9 | Pending |
| EVNT-04 | Phase 9 | Pending |
| WORK-01 | Phase 8 | Pending |
| WORK-02 | Phase 8 | Pending |
| WORK-03 | Phase 8 | Pending |
| WORK-04 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 131 total
- Mapped to phases: 131
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 -- traceability populated by roadmapper*
