# Phase 4: Multi-LLM Abstraction - Research

**Researched:** 2026-03-18
**Domain:** Multi-provider LLM integration, intelligent routing, cost management
**Confidence:** HIGH

## Summary

Phase 4 builds the provider-agnostic LLM abstraction layer that sits between CodeBot's agent layer and external LLM APIs. The primary tool is **LiteLLM** (v1.82+, MIT, ~39K GitHub stars), which provides a unified OpenAI-style interface to 100+ LLM providers with built-in cost tracking, fallback chains, rate limiting, and streaming support. LiteLLM should be used as an **embedded Python SDK** (not as a separate proxy server), since CodeBot is a single Python application that benefits from in-process calls without additional infrastructure.

The design documents specify a detailed architecture with six core components: LLMProvider interface, ModelRouter, FallbackChain, TokenBudgetManager, CostTracker, and RateLimiter. LiteLLM handles most of this natively (provider abstraction, fallbacks, rate limits, cost tracking), but CodeBot needs a custom **task-based routing layer** on top because LiteLLM's built-in routing strategies (simple-shuffle, least-busy, latency-based, cost-based) are load-balancing strategies, not semantic/task-based routing. The project design calls for routing by task type (architecture -> Claude Opus, code generation -> Claude Sonnet, research -> Gemini Pro, etc.), which requires a custom ModelRouter that maps task types to model names and delegates to LiteLLM for execution.

**Primary recommendation:** Use LiteLLM SDK embedded in-process with a custom task-based ModelRouter wrapper. Do NOT use RouteLLM (stale since July 2024, v0.2.0 with no updates). Build the routing table as a YAML-configurable mapping from task types to model+fallback chains. Use LiteLLM's CustomLogger callback for cost tracking integrated with Langfuse for observability.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LLM-01 | Provider-agnostic interface via LiteLLM supporting Anthropic, OpenAI, Google, and self-hosted (Ollama/vLLM) | LiteLLM SDK provides unified `completion()` and `acompletion()` calls with provider prefix convention (`anthropic/claude-opus-4`, `openai/gpt-4o`, `vertex_ai/gemini-2.5-pro`, `ollama/llama3.1:70b`). All providers use identical request/response format. |
| LLM-02 | Route tasks to optimal model by task type, complexity, privacy, cost, and latency via custom routing | RouteLLM is stale (v0.2.0, July 2024, no updates). LiteLLM's built-in routing is load-balancing only. Build custom ModelRouter with YAML-configured task-type-to-model mapping, with complexity and cost adjustments. |
| LLM-03 | Fallback chains (primary model fails -> fallback model) | LiteLLM Router natively supports ordered fallback chains with `fallbacks=[{"model_a": ["model_b", "model_c"]}]`, context window fallbacks, and content policy fallbacks. Also supports deployment ordering via `order` parameter. |
| LLM-04 | Track token usage and cost per agent, per stage, per model | LiteLLM provides `response_cost` in kwargs, `CustomLogger` base class with `log_success_event` / `async_log_success_event`. Built-in cost map covers 100+ models. Integrate with Langfuse for persistent storage and dashboards. |
| LLM-05 | Streaming responses for real-time output | LiteLLM supports `stream=True` on both `completion()` and `acompletion()`. Returns async iterator of chunks. Use `litellm.stream_chunk_builder()` for reconstruction. |
| LLM-06 | Air-gapped operation with self-hosted models only | LiteLLM supports Ollama (`ollama/model`), vLLM (`openai/model` with custom `api_base`), and LocalAI via OpenAI-compatible endpoints. Configuration disables cloud providers when `enabled: false`. |
| LLM-07 | Cost estimates before pipeline execution begins | Build a CostEstimator that uses LiteLLM's model cost map (`litellm.model_cost`) plus task-type routing table to calculate estimated costs before execution starts. |
| LLM-08 | Budget limits halt execution when cost threshold exceeded | LiteLLM's CustomLogger tracks cumulative costs. CostTracker component checks thresholds on every completion and emits budget events (warn at 80%, pause at 90%, abort at 100%). Integration with NATS event bus for pipeline control. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| litellm | 1.82+ | Unified LLM API gateway (SDK mode) | 39K+ GitHub stars, MIT, 100+ providers, built-in cost tracking, 91M monthly PyPI downloads. Industry standard for multi-provider LLM abstraction. |
| langfuse | latest (v3 SDK) | LLM observability, tracing, cost persistence | 23K+ GitHub stars, MIT, OpenTelemetry-based, native LiteLLM integration, self-hostable. Per-agent cost tracking and prompt management. |
| pydantic | >=2.9.0 | Request/response schemas, config validation | Already in project dependencies. Used for all data models per CLAUDE.md conventions. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tiktoken | latest | Token counting for OpenAI models | Cost estimation before API calls, budget checking |
| anthropic | latest | Native Anthropic type hints (optional) | Only if needed for type completeness; LiteLLM handles actual API calls |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LiteLLM SDK (embedded) | LiteLLM Proxy Server | Proxy adds Postgres+Redis infra, useful for multi-team but overkill for single Python app. SDK is zero-overhead, in-process. |
| Custom ModelRouter | RouteLLM (lm-sys) | RouteLLM is **stale** -- last release v0.2.0 in July 2024, no updates since Aug 2024. Only supports strong/weak binary routing. Custom router is more flexible and maintainable. |
| Custom ModelRouter | Not Diamond / Martian | Commercial SaaS routers add latency (20-50ms) and external dependency. Custom is faster, free, and controllable. |
| Langfuse | Custom PostgreSQL logging | Langfuse provides dashboards, prompt management, evaluation tools out of the box. Building custom would be months of work. |

**Installation:**
```bash
# Add to apps/server/pyproject.toml dependencies
uv add litellm langfuse tiktoken
```

**Version verification:** LiteLLM v1.82.2 confirmed on PyPI as of March 13, 2026 (latest release March 16, 2026). Langfuse v3 SDK is OpenTelemetry-based (current). tiktoken is stable.

## Architecture Patterns

### Recommended Project Structure
```
apps/server/src/codebot/llm/
    __init__.py          # Public API: LLMService, get_llm_service()
    service.py           # LLMService facade (main entry point for agents)
    router.py            # TaskBasedModelRouter (task type -> model selection)
    fallback.py          # FallbackChainManager (wraps LiteLLM Router fallbacks)
    budget.py            # TokenBudgetManager + CostTracker
    rate_limiter.py      # RateLimiter (wraps LiteLLM rate limit tracking)
    estimator.py         # CostEstimator (pre-execution cost estimation)
    providers.py         # Provider registry and health checking
    schemas.py           # Pydantic models: LLMRequest, LLMResponse, TokenUsage, etc.
    config.py            # LLM configuration loading from YAML
    callbacks.py         # LiteLLM CustomLogger for cost/usage tracking
    exceptions.py        # Custom exceptions: BudgetExceededError, AllProvidersFailedError, etc.
```

### Pattern 1: LLMService Facade
**What:** A single `LLMService` class that agents interact with. Encapsulates routing, fallback, budgeting, and cost tracking behind one async interface.
**When to use:** Every agent LLM call goes through this service. Agents never call LiteLLM directly.
**Example:**
```python
# Source: CodeBot design docs + LiteLLM SDK patterns
from codebot.llm.service import LLMService
from codebot.llm.schemas import LLMRequest, TaskType

class LLMService:
    """Unified entry point for all LLM calls. Agents use this, never litellm directly."""

    def __init__(
        self,
        config: LLMConfig,
        router: TaskBasedModelRouter,
        budget_manager: TokenBudgetManager,
        cost_tracker: CostTracker,
    ) -> None:
        self._litellm_router = self._build_litellm_router(config)
        self._router = router
        self._budget = budget_manager
        self._cost = cost_tracker

    async def complete(
        self,
        request: LLMRequest,
        *,
        agent_id: str,
        task_type: TaskType,
        stage: str | None = None,
    ) -> LLMResponse:
        """Route, budget-check, execute, track cost."""
        # 1. Route: select model based on task type
        model = self._router.route(task_type, request.constraints)

        # 2. Budget check
        budget_decision = await self._budget.check_budget(
            agent_id=agent_id, estimated_tokens=request.max_tokens
        )
        if not budget_decision.allowed:
            raise BudgetExceededError(agent_id, budget_decision)

        # 3. Execute via LiteLLM (with fallback)
        response = await self._litellm_router.acompletion(
            model=model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )

        # 4. Track cost (callback handles this automatically via CustomLogger)
        return self._parse_response(response)

    async def stream(
        self,
        request: LLMRequest,
        *,
        agent_id: str,
        task_type: TaskType,
    ) -> AsyncIterator[str]:
        """Stream completion with routing and budget checks."""
        model = self._router.route(task_type, request.constraints)
        response = await self._litellm_router.acompletion(
            model=model,
            messages=request.messages,
            stream=True,
        )
        async for chunk in response:
            yield chunk.choices[0].delta.content or ""
```

### Pattern 2: Task-Based Model Router
**What:** Maps CodeBot task types to optimal models using a YAML-configurable routing table.
**When to use:** Every LLM call. The router reads the task type and selects the best model.
**Example:**
```python
# Source: CodeBot SYSTEM_DESIGN.md Section 3.5 + custom design
from dataclasses import dataclass
from codebot.llm.schemas import TaskType, RoutingConstraints

@dataclass(slots=True, kw_only=True)
class RoutingRule:
    primary_model: str
    fallback_models: list[str]
    reason: str

class TaskBasedModelRouter:
    """Routes tasks to optimal models based on task characteristics."""

    # Loaded from configs/llm.yaml at startup
    DEFAULT_ROUTING_TABLE: dict[TaskType, RoutingRule] = {
        TaskType.ORCHESTRATION:     RoutingRule(primary_model="anthropic/claude-opus-4", fallback_models=["openai/gpt-4o", "vertex_ai/gemini-2.5-pro"], reason="Complex planning/reasoning"),
        TaskType.CODE_GENERATION:   RoutingRule(primary_model="anthropic/claude-sonnet-4", fallback_models=["openai/gpt-4o", "vertex_ai/gemini-2.5-pro"], reason="Fast, high-quality code"),
        TaskType.CODE_REVIEW:       RoutingRule(primary_model="anthropic/claude-opus-4", fallback_models=["openai/gpt-4o"], reason="Nuanced code understanding"),
        TaskType.RESEARCH:          RoutingRule(primary_model="vertex_ai/gemini-2.5-pro", fallback_models=["anthropic/claude-opus-4"], reason="Large context, info synthesis"),
        TaskType.SIMPLE_TRANSFORM:  RoutingRule(primary_model="anthropic/claude-haiku-3.5", fallback_models=["vertex_ai/gemini-2.5-flash", "openai/gpt-4o-mini"], reason="Fast, cheap transforms"),
        # ... more task types
    }

    def route(self, task_type: TaskType, constraints: RoutingConstraints | None = None) -> str:
        rule = self._routing_table.get(task_type, self._default_rule)

        # Complexity adjustment
        if constraints and constraints.complexity_score is not None:
            if constraints.complexity_score < 0.3:
                return self._downgrade_model(rule)
            if constraints.complexity_score >= 0.7:
                return rule.primary_model  # ensure premium

        # Cost constraint
        if constraints and constraints.max_cost_per_call:
            return self._find_cheapest_capable(task_type, constraints.max_cost_per_call)

        return rule.primary_model
```

### Pattern 3: LiteLLM CustomLogger for Cost Tracking
**What:** Hooks into every LLM call automatically to record costs, tokens, and latency.
**When to use:** Registered once at startup. Fires on every completion.
**Example:**
```python
# Source: LiteLLM docs - Custom Callbacks
from litellm.integrations.custom_logger import CustomLogger
from codebot.llm.budget import CostTracker

class CodeBotLLMLogger(CustomLogger):
    """Tracks all LLM costs and usage for CodeBot."""

    def __init__(self, cost_tracker: CostTracker, event_bus: EventBus) -> None:
        self._cost = cost_tracker
        self._events = event_bus

    async def async_log_success_event(
        self, kwargs: dict, response_obj, start_time, end_time
    ) -> None:
        cost = kwargs.get("response_cost", 0.0)
        model = kwargs.get("model", "unknown")
        metadata = kwargs.get("litellm_params", {}).get("metadata", {})
        agent_id = metadata.get("agent_id", "unknown")
        stage = metadata.get("stage", "unknown")

        usage = TokenUsage(
            prompt_tokens=response_obj.usage.prompt_tokens,
            completion_tokens=response_obj.usage.completion_tokens,
            total_tokens=response_obj.usage.total_tokens,
            cost_usd=cost,
        )

        # Record in cost tracker
        self._cost.record(agent_id=agent_id, model=model, usage=usage)

        # Emit event for dashboard/pipeline control
        await self._events.publish("llm.usage", {
            "agent_id": agent_id,
            "model": model,
            "stage": stage,
            "cost_usd": cost,
            "tokens": usage.total_tokens,
        })

        # Check budget thresholds
        if self._cost.should_halt():
            await self._events.publish("pipeline.budget_exceeded", {
                "total_cost": self._cost.total_cost_usd,
                "threshold": self._cost.halt_threshold,
            })

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time) -> None:
        model = kwargs.get("model", "unknown")
        error = kwargs.get("exception", "unknown")
        # Log failure for circuit breaker / observability
```

### Pattern 4: Budget-Controlled Execution
**What:** Pre-flight budget check + post-flight cost recording with threshold alerts.
**When to use:** Wraps every LLM call to enforce budget limits.
**Example:**
```python
# Source: CodeBot SYSTEM_DESIGN.md Section 3.7 + 3.8
import asyncio
from collections import defaultdict

class TokenBudgetManager:
    """Per-agent token budgeting with real-time tracking."""

    def __init__(self, global_budget_usd: float, agent_budgets: dict[str, int]) -> None:
        self._global_budget_usd = global_budget_usd
        self._agent_budgets = agent_budgets
        self._usage: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def check_budget(self, agent_id: str, estimated_tokens: int) -> BudgetDecision:
        async with self._lock:
            current = self._usage[agent_id]
            limit = self._agent_budgets.get(agent_id, float("inf"))
            remaining = limit - current
            if estimated_tokens > remaining:
                return BudgetDecision(allowed=False, remaining=remaining)
            return BudgetDecision(allowed=True, remaining=remaining - estimated_tokens)

    async def record_usage(self, agent_id: str, tokens: int) -> None:
        async with self._lock:
            self._usage[agent_id] += tokens
```

### Anti-Patterns to Avoid
- **Direct LiteLLM calls from agents:** Agents must ALWAYS go through `LLMService`. Direct `litellm.completion()` calls bypass routing, budgeting, and cost tracking.
- **Hardcoded model names in agent code:** Model selection is the router's job. Agents specify `task_type`, not model names.
- **Synchronous LLM calls:** All LLM calls must be async (`acompletion`). Sync calls block the event loop and break parallel agent execution.
- **Using LiteLLM Proxy Server:** For CodeBot (single Python app), the SDK is correct. The proxy adds unnecessary infrastructure (separate Postgres, Redis, Docker container).
- **Using RouteLLM:** Stale library (v0.2.0, July 2024). Only supports binary strong/weak routing. Build custom instead.
- **Storing API keys in config files:** Use environment variables referenced by name (e.g., `api_key_env: ANTHROPIC_API_KEY`), never store actual keys.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider API translation | Custom HTTP clients per provider | LiteLLM SDK `completion()` / `acompletion()` | Each provider has different auth, message formats, tool schemas, streaming protocols. LiteLLM handles 100+ providers. |
| Model pricing database | Custom pricing table | LiteLLM `model_cost` map + `response_cost` in callbacks | LiteLLM maintains pricing for 100+ models, updated with each release. Custom pricing gets stale instantly. |
| Rate limiting | Custom token bucket per provider | LiteLLM Router `rpm`/`tpm` limits + cooldown tracking | LiteLLM tracks per-deployment limits, handles cooldowns, supports Redis for distributed tracking. |
| LLM observability/tracing | Custom trace storage and dashboards | Langfuse with LiteLLM integration | Langfuse provides traces, cost dashboards, prompt management, evaluation tools. Building custom is months of work. |
| Retry with exponential backoff | Custom retry loops | LiteLLM Router `num_retries` + fallback chains | LiteLLM handles exponential backoff, cooldowns, and multi-level fallback (deployment -> model group -> fallback chain). |
| Streaming response parsing | Custom SSE parsers per provider | LiteLLM `stream=True` + `stream_chunk_builder()` | Each provider streams differently. LiteLLM normalizes all streams to OpenAI-compatible chunk format. |

**Key insight:** LiteLLM handles the gnarly provider-specific complexity (auth, message format translation, streaming, error mapping, pricing). CodeBot's value-add is the task-based routing layer, budget management, and integration with the agent framework -- things LiteLLM intentionally does not do.

## Common Pitfalls

### Pitfall 1: Streaming Fallback Failures
**What goes wrong:** When streaming is enabled and the primary provider fails mid-stream, the fallback may not activate properly, leaving partial responses.
**Why it happens:** LiteLLM has had historical issues with streaming fallbacks (GitHub issue #6532). Partial stream delivery before error makes fallback tricky.
**How to avoid:** Always set `num_retries` on the Router. For critical operations, consider non-streaming mode. Test fallback behavior with streaming explicitly. Monitor for partial responses.
**Warning signs:** Agents receiving truncated outputs, `AllModelsFailedError` with streaming enabled.

### Pitfall 2: Model Name Mismatches
**What goes wrong:** Using wrong model string format causes silent fallback to wrong provider or 404 errors.
**Why it happens:** LiteLLM uses provider-prefixed model names (`anthropic/claude-opus-4`, `openai/gpt-4o`, `vertex_ai/gemini-2.5-pro`), but the exact strings change with model releases.
**How to avoid:** Centralize all model names in YAML config. Validate model names at startup against LiteLLM's model list. Use constants, never string literals in routing code.
**Warning signs:** `litellm.exceptions.NotFoundError`, unexpected model being used in logs.

### Pitfall 3: Budget Tracking Race Conditions
**What goes wrong:** Parallel agent LLM calls can overshoot budget because budget checks and recordings are not atomic.
**Why it happens:** Multiple agents check budget concurrently, all see "within budget", all proceed, total exceeds limit.
**How to avoid:** Use `asyncio.Lock` for budget check+record operations. Accept small overshoot as acceptable (check is best-effort). The halt threshold should have margin (e.g., warn at 80%, halt at 95%).
**Warning signs:** Total cost exceeding configured budget by more than one call's worth.

### Pitfall 4: Cost Estimation Accuracy
**What goes wrong:** Pre-execution cost estimates are inaccurate because actual token usage depends on LLM response length and retry count.
**Why it happens:** You can estimate input tokens but not output tokens or number of retries/fallbacks.
**How to avoid:** Estimates should use `max_tokens` as worst-case output. Mark estimates as "upper bound". Track actual vs. estimated for calibration over time.
**Warning signs:** Actual costs consistently 2-3x higher than estimates.

### Pitfall 5: Mixing SDK and Proxy
**What goes wrong:** Using LiteLLM SDK inside an app that also routes through a LiteLLM Proxy causes duplicate logic, double counting, and unexpected errors.
**Why it happens:** Both SDK and Proxy contain the same translation layer. Stacking them creates redundancy.
**How to avoid:** Choose ONE: SDK (for CodeBot, this is correct) OR Proxy. Never both in the same request path.
**Warning signs:** Double-counted costs, duplicate log entries, unexpected retries.

### Pitfall 6: Anthropic Message Format Differences
**What goes wrong:** System prompts handled differently by Anthropic (separate `system` parameter) vs. OpenAI (system message in `messages` array).
**Why it happens:** Anthropic API requires system prompt as a top-level parameter, not in the messages array.
**How to avoid:** LiteLLM handles this translation automatically. Do NOT manually extract system messages. Pass standard OpenAI-format messages and let LiteLLM translate.
**Warning signs:** System prompts being ignored or duplicated on Anthropic calls.

## Code Examples

Verified patterns from official sources:

### Initializing LiteLLM Router with Multiple Providers
```python
# Source: LiteLLM Router docs (https://docs.litellm.ai/docs/routing)
import os
from litellm import Router

model_list = [
    # Anthropic models
    {
        "model_name": "claude-opus",
        "litellm_params": {
            "model": "anthropic/claude-opus-4",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
        "model_info": {"id": "anthropic-opus"},
    },
    {
        "model_name": "claude-sonnet",
        "litellm_params": {
            "model": "anthropic/claude-sonnet-4",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
        "model_info": {"id": "anthropic-sonnet"},
    },
    # OpenAI models
    {
        "model_name": "gpt-4o",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "model_info": {"id": "openai-gpt4o"},
    },
    # Google models
    {
        "model_name": "gemini-pro",
        "litellm_params": {
            "model": "vertex_ai/gemini-2.5-pro",
        },
        "model_info": {"id": "google-gemini-pro"},
    },
    # Self-hosted (Ollama)
    {
        "model_name": "ollama-llama",
        "litellm_params": {
            "model": "ollama/llama3.1:70b",
            "api_base": "http://localhost:11434",
        },
        "model_info": {"id": "ollama-llama"},
    },
]

router = Router(
    model_list=model_list,
    num_retries=3,
    fallbacks=[
        {"claude-opus": ["gpt-4o", "gemini-pro"]},
        {"claude-sonnet": ["gpt-4o", "gemini-pro"]},
        {"gpt-4o": ["claude-sonnet", "gemini-pro"]},
    ],
    enable_pre_call_checks=True,
)
```

### Async Streaming Completion
```python
# Source: LiteLLM Streaming docs (https://docs.litellm.ai/docs/completion/stream)
async def stream_completion(router: Router, model: str, messages: list[dict]) -> AsyncIterator[str]:
    response = await router.acompletion(
        model=model,
        messages=messages,
        stream=True,
        metadata={"agent_id": "backend_dev", "stage": "S5"},
    )
    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content
```

### Registering Custom Logger for Cost Tracking
```python
# Source: LiteLLM Custom Callbacks (https://docs.litellm.ai/docs/observability/custom_callback)
import litellm
from litellm.integrations.custom_logger import CustomLogger

class CostTrackingLogger(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        cost = kwargs.get("response_cost", 0.0)
        model = kwargs.get("model", "unknown")
        metadata = kwargs.get("litellm_params", {}).get("metadata", {})
        # ... store in CostTracker, emit events

# Register at startup
logger = CostTrackingLogger()
litellm.callbacks = [logger]
```

### Self-Hosted Model (Ollama) Completion
```python
# Source: LiteLLM Getting Started (https://docs.litellm.ai/docs/)
from litellm import acompletion

response = await acompletion(
    model="ollama/llama3.1:70b",
    messages=[{"role": "user", "content": "Explain this code..."}],
    api_base="http://localhost:11434",
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| RouteLLM for smart routing | Custom task-based routing + LiteLLM load balancing | RouteLLM stale since July 2024 | Build custom router; RouteLLM only supports binary strong/weak routing anyway |
| LiteLLM as separate proxy | LiteLLM SDK embedded in-process | SDK has parity with proxy for single-app use | No extra infrastructure needed (no separate Postgres/Redis for proxy) |
| Manual provider SDKs | LiteLLM unified interface | LiteLLM v1.82+ (March 2026) | 100+ providers via one API, automatic cost tracking |
| Custom observability | Langfuse v3 (OpenTelemetry-based) | Langfuse v3 SDK current | OTEL-native, automatic LiteLLM integration, rich dashboards |
| Per-provider rate limiting | LiteLLM Router RPM/TPM + cooldowns | Built into Router | Automatic cooldown, distributed tracking via Redis optional |

**Deprecated/outdated:**
- **RouteLLM** (lm-sys): Last release v0.2.0 (July 2024). No updates since August 2024. Do not use.
- **LiteLLM Proxy for single-app use**: Overkill when SDK provides equivalent functionality without infra overhead.
- **Direct provider SDK calls**: Bypass all routing, fallback, cost tracking. Use LiteLLM instead.
- **Hardcoded model pricing**: LiteLLM maintains `model_cost` map. Custom pricing tables go stale immediately.

## Open Questions

1. **Provider-specific tool calling differences**
   - What we know: LiteLLM normalizes tool call format to OpenAI-compatible. Anthropic, Google, and OpenAI all support tool use.
   - What's unclear: How well LiteLLM handles tool call translation for complex multi-tool scenarios when falling back between providers with different tool support levels.
   - Recommendation: Test tool calling with fallback scenarios in Phase 4 integration tests. If issues found, restrict fallbacks for tool-heavy tasks to providers with verified tool support.

2. **Langfuse deployment model**
   - What we know: Langfuse is self-hostable (MIT). Can run alongside CodeBot's Postgres/Redis.
   - What's unclear: Whether Langfuse should share CodeBot's Postgres or use a separate instance. Resource impact of high-volume LLM tracing.
   - Recommendation: Use Langfuse cloud for development, self-host for production. Defer deployment decision to Phase 10 (server). For now, use Langfuse SDK with cloud endpoint.

3. **Google Vertex AI vs. Google AI Studio authentication**
   - What we know: LiteLLM supports both `vertex_ai/` prefix (service account auth, gcloud) and `gemini/` prefix (API key auth, simpler).
   - What's unclear: Which auth path is more reliable for production. Vertex AI requires GCP project setup.
   - Recommendation: Use `gemini/` prefix with API key for simplicity in v1. Document Vertex AI path for enterprise users.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio |
| Config file | `apps/server/pyproject.toml` (exists, `asyncio_mode = "auto"`) |
| Quick run command | `cd apps/server && uv run pytest tests/unit/llm/ -x -q` |
| Full suite command | `cd apps/server && uv run pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LLM-01 | Unified completion across Anthropic, OpenAI, Google, Ollama | unit | `uv run pytest tests/unit/llm/test_service.py::test_complete_anthropic -x` | Wave 0 |
| LLM-01 | Provider-agnostic interface returns consistent LLMResponse | unit | `uv run pytest tests/unit/llm/test_service.py::test_response_format_consistency -x` | Wave 0 |
| LLM-02 | Task-based routing selects correct model per task type | unit | `uv run pytest tests/unit/llm/test_router.py::test_task_routing -x` | Wave 0 |
| LLM-02 | Complexity adjustment downgrades/upgrades model | unit | `uv run pytest tests/unit/llm/test_router.py::test_complexity_adjustment -x` | Wave 0 |
| LLM-03 | Fallback activates when primary model fails | unit | `uv run pytest tests/unit/llm/test_fallback.py::test_fallback_chain -x` | Wave 0 |
| LLM-03 | InvalidRequestError does NOT trigger fallback | unit | `uv run pytest tests/unit/llm/test_fallback.py::test_no_fallback_on_bad_request -x` | Wave 0 |
| LLM-04 | Token usage tracked per agent, per model | unit | `uv run pytest tests/unit/llm/test_budget.py::test_cost_tracking_per_agent -x` | Wave 0 |
| LLM-04 | Cost breakdown queryable by agent, stage, model | unit | `uv run pytest tests/unit/llm/test_budget.py::test_cost_report -x` | Wave 0 |
| LLM-05 | Streaming returns async iterator of chunks | unit | `uv run pytest tests/unit/llm/test_service.py::test_streaming -x` | Wave 0 |
| LLM-06 | Air-gapped mode with only self-hosted models | unit | `uv run pytest tests/unit/llm/test_config.py::test_air_gapped_config -x` | Wave 0 |
| LLM-07 | Cost estimation before execution | unit | `uv run pytest tests/unit/llm/test_estimator.py::test_pre_execution_estimate -x` | Wave 0 |
| LLM-08 | Budget threshold halts execution | unit | `uv run pytest tests/unit/llm/test_budget.py::test_budget_halt -x` | Wave 0 |
| LLM-08 | Budget warning at 80% threshold | unit | `uv run pytest tests/unit/llm/test_budget.py::test_budget_warning -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/server && uv run pytest tests/unit/llm/ -x -q`
- **Per wave merge:** `cd apps/server && uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/llm/test_service.py` -- covers LLM-01, LLM-05
- [ ] `tests/unit/llm/test_router.py` -- covers LLM-02
- [ ] `tests/unit/llm/test_fallback.py` -- covers LLM-03
- [ ] `tests/unit/llm/test_budget.py` -- covers LLM-04, LLM-08
- [ ] `tests/unit/llm/test_config.py` -- covers LLM-06
- [ ] `tests/unit/llm/test_estimator.py` -- covers LLM-07
- [ ] `tests/unit/llm/conftest.py` -- shared fixtures (mock LiteLLM Router, mock providers, mock event bus)
- [ ] Framework install: `uv add --dev pytest-asyncio` (verify version in pyproject.toml)

**Critical testing convention from CLAUDE.md:** "Mock LLM providers in tests -- never call real APIs." All tests must mock LiteLLM's completion/acompletion calls.

## Sources

### Primary (HIGH confidence)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm) - 39K+ stars, MIT license, active development (releases March 2026)
- [LiteLLM Docs - Getting Started](https://docs.litellm.ai/docs/) - Provider naming conventions, completion API
- [LiteLLM Docs - Router](https://docs.litellm.ai/docs/routing) - Load balancing, routing strategies, fallback configuration
- [LiteLLM Docs - Streaming](https://docs.litellm.ai/docs/completion/stream) - Async/sync streaming patterns
- [LiteLLM Docs - Custom Callbacks](https://docs.litellm.ai/docs/observability/custom_callback) - CustomLogger class, response_cost tracking
- [LiteLLM Docs - Fallbacks](https://docs.litellm.ai/docs/proxy/reliability) - Fallback types (default, context window, content policy)
- [LiteLLM Docs - Budgets](https://docs.litellm.ai/docs/proxy/users) - Per-user budget limits, budget duration
- [LiteLLM PyPI](https://pypi.org/project/litellm/) - v1.82.2 confirmed March 13, 2026
- [RouteLLM GitHub](https://github.com/lm-sys/RouteLLM) - v0.2.0, last release July 2024, **stale** (no updates since Aug 2024)
- [Langfuse Docs](https://langfuse.com/docs) - v3 SDK, OpenTelemetry-based
- [Langfuse + LiteLLM Integration](https://langfuse.com/docs/integrations/litellm/tracing) - Integration patterns

### Secondary (MEDIUM confidence)
- [LiteLLM Review 2026](https://www.truefoundry.com/blog/a-detailed-litellm-review-features-pricing-pros-and-cons-2026) - SDK vs Proxy decision matrix
- [DataCamp LiteLLM Tutorial](https://www.datacamp.com/tutorial/litellm) - Practical streaming + fallback examples
- [Top 5 LLM Router Solutions 2026](https://www.getmaxim.ai/articles/top-5-llm-router-solutions-in-2026/) - Routing landscape overview
- [Not-Diamond awesome-ai-model-routing](https://github.com/Not-Diamond/awesome-ai-model-routing) - Comprehensive routing tool list

### Tertiary (LOW confidence)
- [RouteLLM production readiness claims](https://routellm.dev/) - Marketing claims from RouteLLM website; project appears unmaintained. Needs validation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - LiteLLM is mature (39K stars, 91M monthly downloads), actively maintained, MIT licensed. Langfuse is well-established (23K stars).
- Architecture: HIGH - Design docs provide detailed component specifications. LiteLLM SDK patterns align well with project architecture. Custom task-based router is straightforward.
- Pitfalls: HIGH - Streaming fallback issues documented in GitHub issues. Budget race conditions are a known distributed systems pattern. Provider format differences well-documented.
- RouteLLM assessment: HIGH - Verified on PyPI (v0.2.0, July 2024) and GitHub (no commits since Aug 2024). Confirmed stale.

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (LiteLLM releases frequently; check for breaking changes in new versions)
