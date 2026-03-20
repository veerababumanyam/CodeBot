# Phase 7: Vertical Slice - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase proves the entire CodeBot architecture end-to-end with a minimal 5-agent pipeline (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger). A user describes a project idea in natural language and gets working, tested, reviewed Python/FastAPI code out the other end. Scope is narrow (single project type: greenfield Python/FastAPI) but deep (requirement extraction through tested code with debug-fix loop).

</domain>

<decisions>
## Implementation Decisions

### Input Processing & Requirement Extraction
- Single LLM call with instructor for structured Pydantic output schema, one-pass extraction
- Ambiguous requirements are auto-inferred with disclaimer -- flag low-confidence items, continue autonomously
- Warn above 20 functional requirements about scope, but continue
- NL-only input for vertical slice -- structured PRD support (Markdown/JSON/YAML) deferred to Phase 9

### Code Generation & Review Quality
- Backend Dev generates a single FastAPI app (main.py, models, routes, business logic in one module)
- Code Reviewer outputs structured review with severity levels (CRITICAL/WARNING/INFO per finding, quality gate pass/fail)
- Pipeline blocks on CRITICAL findings only -- warnings reported but don't block advancement
- Generated code includes Google-style docstrings on public API (consistent with CLAUDE.md convention)

### Debug-Fix Loop & Pipeline Behavior
- 3 max retry iterations for debug-fix loop (diminishing returns after 3)
- Debugger uses experiment branches with keep/discard semantics -- each fix is a branch, merged only if tests improve
- Circuit breakers: max retries + no-improvement detection (stop if test pass count doesn't increase)
- All agent and pipeline transitions emit NATS events (proves EVNT-01, enables future dashboard)

### Claude's Discretion
- Internal agent prompt engineering and system prompt design
- Specific Pydantic schema field names for requirement extraction models
- Test fixture structure and mock patterns for agent unit tests

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/server/src/codebot/agent_config/loader.py` -- YAML agent config loader
- `configs/agents/orchestrator.yaml` -- existing orchestrator config template
- `apps/server/src/codebot/llm/service.py` -- LLMService facade with routing, fallback, streaming
- `apps/server/src/codebot/context/` -- 3-tier context module (L0/L1/L2)
- `apps/server/src/codebot/pipeline/` -- full pipeline module (workflows, activities, gates, registry, events)
- `apps/server/src/codebot/events/bus.py` -- NATS JetStream event bus

### Established Patterns
- BaseAgent PRA cycle defined in Phase 3 (agent_config module has loader, no agents/ dir yet)
- Pipeline uses Temporal workflows with phase activities and gate checks
- LLM calls go through LLMService with task-based routing and cost tracking
- All models use Pydantic v2 with frozen=True ConfigDict for immutability
- Dataclasses use slots=True and kw_only=True per CLAUDE.md

### Integration Points
- Agents will live in `apps/server/src/codebot/agents/` (new directory)
- Pipeline graph defined via YAML in `configs/pipelines/vertical-slice.yaml`
- Agent YAML configs in `configs/agents/` (orchestrator.yaml exists as template)
- Events emitted via PipelineEventEmitter from Phase 6

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches based on research and existing architecture.

</specifics>

<deferred>
## Deferred Ideas

- Structured PRD input (Markdown/JSON/YAML) -- deferred to Phase 9 (Full Agent Roster)
- Full worktree isolation for coding agents -- deferred to Phase 8
- Frontend/Mobile/Infrastructure code generation -- deferred to Phase 9

</deferred>
