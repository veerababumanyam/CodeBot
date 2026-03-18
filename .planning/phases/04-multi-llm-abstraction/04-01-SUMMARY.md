---
phase: 04-multi-llm-abstraction
plan: 01
subsystem: llm
tags: [litellm, pydantic, yaml, routing, multi-llm, langfuse, budget]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "pyproject.toml, Settings class, EventType enum"
  - phase: 03-agent-framework
    provides: "AgentConfig patterns, agent-sdk enums"
provides:
  - "TaskType enum mapping 12 task categories to model selection"
  - "LLMRequest/LLMResponse/TokenUsage Pydantic v2 schemas"
  - "RoutingRule and RoutingConstraints models"
  - "BudgetDecision model for budget management"
  - "LLMConfig YAML loader with provider and routing table validation"
  - "ProviderRegistry with health tracking and LiteLLM model list builder"
  - "TaskBasedModelRouter with complexity, cost, and local-preference routing"
  - "Custom exceptions: BudgetExceededError, AllProvidersFailedError, ModelNotFoundError"
  - "Default llm.yaml config with 8 models across 4 providers"
affects: [04-multi-llm-abstraction, 06-pipeline-orchestration, 08-security-pipeline-worktree-manager]

# Tech tracking
tech-stack:
  added: [litellm, langfuse, pyyaml]
  patterns: [YAML-based config loading, tier-based model routing, provider health tracking, frozen Pydantic models]

key-files:
  created:
    - apps/server/src/codebot/llm/__init__.py
    - apps/server/src/codebot/llm/schemas.py
    - apps/server/src/codebot/llm/exceptions.py
    - apps/server/src/codebot/llm/config.py
    - apps/server/src/codebot/llm/providers.py
    - apps/server/src/codebot/llm/router.py
    - configs/providers/llm.yaml
    - apps/server/tests/unit/llm/conftest.py
    - apps/server/tests/unit/llm/test_schemas.py
    - apps/server/tests/unit/llm/test_config.py
    - apps/server/tests/unit/llm/test_router.py
  modified:
    - apps/server/pyproject.toml
    - apps/server/src/codebot/config.py
    - libs/agent-sdk/src/agent_sdk/models/enums.py

key-decisions:
  - "frozen=True ConfigDict on immutable Pydantic models (TokenUsage, BudgetDecision, RoutingRule, LLMResponse)"
  - "Three-tier model classification (PREMIUM/STANDARD/ECONOMY) for automatic downgrade routing"
  - "DOWNGRADE_MAP for premium-to-standard model mapping (opus->sonnet, gpt-4o->gpt-4o-mini, gemini-pro->gemini-flash)"
  - "Complexity threshold 0.3 for downgrade, 0.7 for ensuring premium"
  - "Provider unhealthy after 3 consecutive failures (_UNHEALTHY_THRESHOLD = 3)"
  - "tiktoken already present from Phase 5 -- not re-added to dependencies"

patterns-established:
  - "YAML config loading via Pydantic model_validate with yaml.safe_load"
  - "Provider health tracking with consecutive failure counting"
  - "Task-based routing with constraint priority: prefer_local > complexity > cost > default"
  - "Frozen Pydantic models for immutable response/decision types"

requirements-completed: [LLM-01, LLM-02, LLM-06]

# Metrics
duration: 9min
completed: 2026-03-18
---

# Phase 4 Plan 01: Multi-LLM Foundation Summary

**Task-based LLM router with 12 task types, YAML provider config (8 models), and complexity/cost-aware model selection using litellm**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-18T18:29:49Z
- **Completed:** 2026-03-18T18:39:30Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- TaskType enum mapping all 12 CodeBot task categories to model selection strategies
- Full Pydantic v2 schema suite (LLMRequest, LLMResponse, TokenUsage, RoutingRule, RoutingConstraints, BudgetDecision) with frozen immutable models
- YAML-based config loading with validation for providers, routing tables, budgets, and fallback settings
- ProviderRegistry with health tracking (failure counting, automatic unhealthy marking) and LiteLLM model list builder
- TaskBasedModelRouter with complexity-based downgrade, cost-constrained selection, and self-hosted preference
- Default llm.yaml with 8 models across Anthropic (3), OpenAI (2), Google (2), and Ollama (1)
- 95 unit tests passing, mypy strict clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies, create LLM schemas, exceptions, and event types** - `8c1fe5b` (feat)
2. **Task 2: Create YAML config loading and provider registry** - `fb5817b` (feat)
3. **Task 3: Create TaskBasedModelRouter with complexity and cost adjustments** - `830a66f` (feat)

## Files Created/Modified
- `apps/server/src/codebot/llm/__init__.py` - Package init with module docstring
- `apps/server/src/codebot/llm/schemas.py` - TaskType, LLMRequest, LLMResponse, TokenUsage, RoutingRule, RoutingConstraints, BudgetDecision
- `apps/server/src/codebot/llm/exceptions.py` - LLMError hierarchy: BudgetExceededError, AllProvidersFailedError, ModelNotFoundError, ProviderUnavailableError
- `apps/server/src/codebot/llm/config.py` - LLMConfig YAML loading with ProviderConfig, BudgetConfig, FallbackConfig, LLMSettings
- `apps/server/src/codebot/llm/providers.py` - ProviderRegistry with health tracking and LiteLLM model list builder
- `apps/server/src/codebot/llm/router.py` - TaskBasedModelRouter with ModelTier enum, DOWNGRADE_MAP, tier-based routing
- `configs/providers/llm.yaml` - Default config with 8 models, 12 routing rules, budget and fallback settings
- `apps/server/pyproject.toml` - Added litellm, langfuse, pyyaml dependencies
- `apps/server/src/codebot/config.py` - Added llm_config_path to Settings
- `libs/agent-sdk/src/agent_sdk/models/enums.py` - Added LLM_USAGE, LLM_FAILURE, BUDGET_WARNING, BUDGET_EXCEEDED event types
- `apps/server/tests/unit/llm/conftest.py` - Shared fixtures (sample_messages, sample_routing_rule, mock_litellm_response)
- `apps/server/tests/unit/llm/test_schemas.py` - 45 tests for schemas, exceptions, and event types
- `apps/server/tests/unit/llm/test_config.py` - 26 tests for config loading, air-gapped mode, and provider registry
- `apps/server/tests/unit/llm/test_router.py` - 24 tests for router strategies and fallback chains

## Decisions Made
- Used frozen=True ConfigDict on immutable models (TokenUsage, BudgetDecision, RoutingRule, LLMResponse) for thread safety
- Three-tier model classification (PREMIUM/STANDARD/ECONOMY) enables automatic downgrade for low-complexity tasks
- Complexity threshold 0.3 for downgrade, 0.7 for ensuring premium selection
- Provider marked unhealthy after 3 consecutive failures (configurable threshold)
- tiktoken already present from Phase 5 context management -- not re-added to avoid duplicate dependency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All type contracts ready for Plan 02 to wire into full LLMService facade
- ProviderRegistry.build_litellm_model_list() ready for LiteLLM Router integration
- TaskBasedModelRouter ready for LLMService to call during request routing
- Schemas ready for budget tracking, cost calculation, and observability

## Self-Check: PASSED

All 11 created files verified present. All 3 task commits (8c1fe5b, fb5817b, 830a66f) verified in git log.

---
*Phase: 04-multi-llm-abstraction*
*Completed: 2026-03-18*
