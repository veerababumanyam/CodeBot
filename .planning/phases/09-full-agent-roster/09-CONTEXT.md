# Phase 9: Full Agent Roster - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements all 30 specialized agents across the 10 SDLC stages (S0-S9), completing the full pipeline from brainstorming through documentation. Each agent follows the uniform BaseAgent PRA cycle with YAML configuration. Stage subgraphs compose agents for parallel execution (S3, S5, S6). The 5 agents from Phase 7 (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger) are already implemented — this phase adds the remaining 25.

</domain>

<decisions>
## Implementation Decisions

### Agent Registration & Configuration
- All 30 agents share the uniform BaseAgent PRA cycle (perceive/reason/act/review) — differences via YAML config (tools, prompts, models)
- Stage subgraphs defined in YAML: `configs/stages/s1-brainstorm.yaml` etc., loaded by graph engine
- Model assignment per agent via YAML config — premium for complex agents (Architect, Backend Dev), economy for simple (i18n, Formatter)
- Tool registry pattern — shared tool instances registered centrally, agents reference by name in YAML

### Stage Execution Patterns
- S3 (Architecture) parallel agents merge via MERGE node — each outputs typed artifacts, merge combines into unified architecture doc
- S5 (Implementation) uses project type detection from Phase 6 to skip irrelevant platform agents (no Frontend for backend-only)
- S6 (QA) quality gates use all-must-pass — every QA agent's gate must pass before advancing to Testing
- S9 (Documentation) agents generate from both code analysis and prior pipeline artifacts

### Agent Complexity & Testing
- Full PRA cycle with LLM calls for every agent — real prompt templates and structured output models (no stubs)
- 1 test file per agent — consistent pattern with mocked LLM, all 30 agents tested individually
- Prompt templates inline in agent class as class constants — self-contained, no external template files
- Full registry integration test verifying all 30 agents load, instantiate, and respond to mock input

### Claude's Discretion
- Individual agent prompt engineering and system prompt content
- Specific structured output Pydantic models per agent
- Tool binding details for each agent category

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/server/src/codebot/agents/` — 5 agents from Phase 7 (orchestrator, backend_dev, code_reviewer, tester, debugger)
- `apps/server/src/codebot/agent_config/loader.py` — YAML agent config loader
- `configs/agents/` — 5 existing YAML configs as templates
- `apps/server/src/codebot/security/orchestrator.py` — SecurityOrchestrator for QA security agent
- `apps/server/src/codebot/worktree/` — WorktreePool for implementation agent isolation

### Established Patterns
- BaseAgent PRA cycle: perceive() -> reason() -> act() -> review()
- Agent YAML config: model, tools, context_tiers, retry_policy, system_prompt_ref
- instructor + LiteLLM for structured output extraction
- Pydantic v2 models for all agent I/O schemas

### Integration Points
- New agents go in `apps/server/src/codebot/agents/`
- YAML configs in `configs/agents/`
- Stage subgraph configs in `configs/stages/` (new directory)
- Tests in `tests/unit/agents/`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow AGENT_CATALOG.md for detailed specs per agent.

</specifics>

<deferred>
## Deferred Ideas

- Agent hot-reload without restart — deferred to post-v1.0
- Agent marketplace/sharing — deferred to post-v1.0
- Custom user-defined agents — handled by Creator agents in Phase 11

</deferred>
