---
phase: 09-full-agent-roster
plan: 01
subsystem: agents
tags: [agent-registry, brainstorming, researcher, pra-cycle, yaml-config]

# Dependency graph
requires:
  - phase: 03-agent-framework
    provides: BaseAgent with PRA cycle, AgentStateMachine, AgentMetrics
provides:
  - AgentRegistry with register_agent decorator and create_agent factory
  - BrainstormingAgent for S1 pipeline stage (BRST-01 to BRST-07)
  - ResearcherAgent for S2 pipeline stage (RSRC-01 to RSRC-04)
  - Shared test conftest with mock_llm, mock_event_bus, mock_context_manager fixtures
affects: [09-02, 09-03, 09-04, 09-05, pipeline-orchestration]

# Tech tracking
tech-stack:
  added: []
  patterns: [register_agent-decorator, yaml-agent-config, pra-cycle-agent-pattern]

key-files:
  created:
    - apps/server/src/codebot/agents/registry.py
    - apps/server/src/codebot/agents/brainstorming.py
    - apps/server/src/codebot/agents/researcher.py
    - configs/agents/brainstorming.yaml
    - configs/agents/researcher.yaml
    - tests/unit/agents/conftest.py
    - tests/unit/agents/test_agent_registry.py
    - tests/unit/agents/test_brainstorming.py
    - tests/unit/agents/test_researcher.py
  modified:
    - apps/server/src/codebot/agents/__init__.py

key-decisions:
  - "AgentRegistry uses module-level dict with decorator registration (no metaclass complexity)"
  - "Registry warns on overwrite instead of raising -- allows test fixtures to re-register"
  - "BrainstormingAgent and ResearcherAgent follow identical PRA pattern for consistency"
  - "BaseAgent already existed from Phase 3 -- no stub needed"

patterns-established:
  - "@register_agent(AgentType.XXX) decorator pattern for self-registering agent classes"
  - "YAML config per agent in configs/agents/ with agent_type, model, tools, context_tiers, retry_policy"
  - "SYSTEM_PROMPT module-level constant with role/responsibilities/output_format/constraints sections"
  - "conftest.py mock fixtures for LLM, EventBus, ContextManager, Tools reusable across all agent tests"

requirements-completed: [AGNT-08, BRST-01, BRST-02, BRST-03, BRST-04, BRST-05, BRST-06, BRST-07, RSRC-01, RSRC-02, RSRC-03, RSRC-04]

# Metrics
duration: 6min
completed: 2026-03-20
---

# Phase 9 Plan 01: Agent Registry, Brainstorming, and Researcher Summary

**AgentRegistry with decorator pattern plus BrainstormingAgent (S1) and ResearcherAgent (S2) with YAML configs and PRA cycle implementations**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T08:30:29Z
- **Completed:** 2026-03-20T08:36:08Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- AgentRegistry module with register_agent decorator, create_agent factory, and get_all_registered for all 30 agents to use
- BrainstormingAgent implementing S1 brainstorming stage with PRA cycle covering 7 BRST requirements
- ResearcherAgent implementing S2 research stage with PRA cycle covering 4 RSRC requirements
- Shared test conftest with mock_llm, mock_event_bus, mock_context_manager, mock_tools for reuse across all agent tests
- 23 new unit tests all passing (4 registry + 10 brainstorming + 9 researcher)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AgentRegistry, test scaffolding, and shared agent conftest** - `f75f4b5` (feat)
2. **Task 2: Implement BrainstormingAgent with YAML config and tests** - `5576038` (feat)
3. **Task 3: Implement ResearcherAgent with YAML config and tests** - `d31351d` (feat)

## Files Created/Modified
- `apps/server/src/codebot/agents/registry.py` - AgentRegistry with register_agent decorator, create_agent factory, get_all_registered
- `apps/server/src/codebot/agents/__init__.py` - Updated to re-export registry functions
- `apps/server/src/codebot/agents/brainstorming.py` - BrainstormingAgent(BaseAgent) with PRA cycle for S1 stage
- `apps/server/src/codebot/agents/researcher.py` - ResearcherAgent(BaseAgent) with PRA cycle for S2 stage
- `configs/agents/brainstorming.yaml` - YAML config for BrainstormingAgent (tier1, temperature 0.7)
- `configs/agents/researcher.yaml` - YAML config for ResearcherAgent (tier1, temperature 0.3)
- `tests/unit/agents/conftest.py` - Shared mock fixtures (mock_llm, mock_event_bus, mock_context_manager, mock_tools)
- `tests/unit/agents/test_agent_registry.py` - 4 tests for registry register/create/list/copy
- `tests/unit/agents/test_brainstorming.py` - 10 tests for BrainstormingAgent
- `tests/unit/agents/test_researcher.py` - 9 tests for ResearcherAgent

## Decisions Made
- AgentRegistry uses module-level dict with decorator registration (no metaclass complexity needed for 30 agents)
- Registry warns on overwrite instead of raising, enabling test fixtures to safely re-register agent types
- BaseAgent from Phase 3 already had full PRA cycle implementation -- no stub needed
- Both new agents follow identical structural pattern (PRA methods, SYSTEM_PROMPT constant, build_system_prompt method) for consistency

## Deviations from Plan

None - plan executed exactly as written. BaseAgent already existed from Phase 3, so the stub creation step in Task 1.0 was skipped as the plan anticipated.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Registry pattern established for Plans 02-05 to add remaining 23 agents
- Test conftest fixtures ready for all future agent tests
- Both agents follow the pattern all subsequent agents will replicate

## Self-Check: PASSED

All 10 created/modified files verified present. All 3 task commits verified in git log.

---
*Phase: 09-full-agent-roster*
*Completed: 2026-03-20*
