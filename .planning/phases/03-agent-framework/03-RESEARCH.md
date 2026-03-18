# Phase 3: Agent Framework - Research

**Researched:** 2026-03-18
**Domain:** Python async agent framework -- BaseAgent, state machine, YAML config, PRA cognitive cycle, recovery, metrics
**Confidence:** HIGH

## Summary

Phase 3 builds the agent execution layer on top of the graph engine (Phase 2). The core deliverable is a `BaseAgent` abstract class implementing the Perception-Reasoning-Action (PRA) cognitive cycle, wrapped in an `AgentNode` adapter for graph execution, governed by a finite state machine (IDLE -> INITIALIZING -> EXECUTING -> REVIEWING -> COMPLETED/FAILED -> RECOVERING), and fully configurable via YAML without code changes. Recovery strategies (retry with modified prompt, model fallback, escalation, rollback) must be configurable per agent.

The existing codebase from Phase 1 provides: ORM models for Agent/AgentExecution with AgentType (30 types) and AgentStatus enums, Pydantic schemas in `agent-sdk`, EventEnvelope/AgentEvent models for NATS publishing, and the EventBus. Phase 2 will provide the graph engine, SharedState, and node execution infrastructure. Phase 3 creates the agent runtime that connects these layers.

**Primary recommendation:** Build the agent framework as a set of Python dataclasses/Pydantic models in `libs/agent-sdk` (BaseAgent, AgentConfig, state machine) with the `AgentNode` adapter in `libs/graph-engine`. Use a hand-rolled finite state machine (not a library) since the agent FSM has only 7 states and the overhead of python-statemachine would outweigh the benefit. YAML configs validate through Pydantic models. Recovery strategies are composable classes following the Strategy pattern.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-01 | All agents extend BaseAgent with PRA cognitive cycle | BaseAgent abstract class with `perceive()`, `reason()`, `act()`, `review()` methods; PRA loop in `execute()` |
| AGNT-02 | AgentNode wraps BaseAgent for graph execution with typed I/O | AgentNode adapter in graph-engine; accepts SharedState input, returns SharedState output; delegates to BaseAgent.execute() |
| AGNT-03 | Agent state machine: IDLE -> INITIALIZING -> EXECUTING -> REVIEWING -> COMPLETED/FAILED -> RECOVERING | Enum-based FSM with transition validation; emits AgentEvent on every transition via EventBus |
| AGNT-04 | Each coding agent operates in isolated git worktree | Stub interface for WorktreeManager (actual implementation in Phase 8); AgentNode accepts optional worktree_path |
| AGNT-05 | Agent configs are declarative YAML (system prompt, tools, model, context tiers, retry policy) | Pydantic AgentConfig model validates YAML; AgentConfigLoader discovers and loads configs from `configs/agents/` |
| AGNT-06 | Agents self-review output against acceptance criteria before COMPLETED | `review()` method in PRA cycle; transition from EXECUTING to REVIEWING to COMPLETED/FAILED |
| AGNT-07 | Failed agents trigger recovery (retry with modified prompt, escalate, rollback) | RecoveryStrategy base class with RetryWithModifiedPrompt, EscalateToHuman, Rollback implementations |
| AGNT-12 | Agent metrics: execution time, token usage, cost, success rate, retry count | AgentMetrics dataclass populated during execution; persisted to AgentExecution ORM; emitted as events |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Required by project; asyncio.TaskGroup, ExceptionGroup |
| Pydantic | >=2.9.0 | YAML config validation, agent schemas | Already in project; v2 with ConfigDict, field_validator, model_validator |
| PyYAML | >=6.0 | YAML parsing for agent configs | Standard Python YAML parser; already installed (6.0.3) |
| SQLAlchemy | >=2.0.35 | ORM for Agent/AgentExecution persistence | Already in project; async with asyncpg |
| structlog | (not yet installed) | Structured logging for state transitions | Consider adding; stdlib logging sufficient for now |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| GitPython | >=3.1.0 | Git worktree stub interface | Phase 3 defines the interface only; Phase 8 implements full worktree isolation |
| nats-py | >=2.9.0 | Event publishing for state transitions | Already in project via EventBus |
| pydantic-settings | >=2.5.0 | Environment-based config overrides | Already in project |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled FSM | python-statemachine 3.0.0 | Only 7 states, 9 transitions -- library adds dependency and complexity for minimal gain. Hand-rolled is simpler, fully typed, zero-dep. |
| dataclass BaseAgent | Pydantic BaseModel BaseAgent | Pydantic adds serialization overhead per-cycle; dataclass with `slots=True, kw_only=True` is the project convention for runtime objects (Pydantic for API/config, dataclass for internal) |
| YAML-only config | Python-only config | YAML enables non-developer configuration, agent marketplace, and hot-reload without code changes -- a Phase 3 requirement (AGNT-05) |

**Installation:**
```bash
# No new dependencies needed for Phase 3.
# All required packages already in pyproject.toml:
# pydantic, pyyaml, sqlalchemy, nats-py
# GitPython is already installed (3.1.x) -- interface-only usage in Phase 3
```

## Architecture Patterns

### Recommended Project Structure

```
libs/agent-sdk/src/agent_sdk/
  models/
    enums.py              # (EXISTS) AgentType, AgentStatus, ExecutionStatus
    agent.py              # (EXISTS) AgentSchema, AgentExecutionSchema
    events.py             # (EXISTS) AgentEvent, EventEnvelope
    agent_config.py       # (NEW) Pydantic models for YAML agent config
  agents/
    __init__.py           # (NEW) Package init
    base.py               # (NEW) BaseAgent abstract class with PRA cycle
    state_machine.py      # (NEW) AgentStateMachine with transition validation
    recovery.py           # (NEW) RecoveryStrategy hierarchy
    metrics.py            # (NEW) AgentMetrics collector

libs/graph-engine/src/graph_engine/
    nodes/
      agent_node.py       # (NEW) AgentNode wrapping BaseAgent for graph execution

apps/server/src/codebot/
    agents/               # (NEW) Directory for concrete agent implementations (Phase 9)
      __init__.py
    config/
      agent_loader.py     # (NEW) YAML config discovery and loading

configs/
    agents/               # (NEW) YAML agent configuration files
      _schema.yaml        # (NEW) Example/template config
      orchestrator.yaml   # (NEW) Orchestrator agent config (reference implementation)
```

### Pattern 1: BaseAgent with PRA Cognitive Cycle

**What:** Abstract base class implementing the Perception-Reasoning-Action loop from MASFactory (arXiv:2603.06007). Each agent executes a bounded loop of perceive -> reason -> act -> review.

**When to use:** Every agent in the system extends BaseAgent.

**Example:**
```python
# libs/agent-sdk/src/agent_sdk/agents/base.py
from __future__ import annotations

import abc
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agent_sdk.models.enums import AgentStatus, AgentType

if TYPE_CHECKING:
    from agent_sdk.agents.state_machine import AgentStateMachine
    from agent_sdk.agents.metrics import AgentMetrics

@dataclass(slots=True, kw_only=True)
class AgentInput:
    """Typed input to an agent from the graph engine."""
    task_id: uuid.UUID
    shared_state: dict[str, Any]
    context_tiers: dict[str, Any]  # l0, l1, l2

@dataclass(slots=True, kw_only=True)
class AgentOutput:
    """Typed output from an agent to the graph engine."""
    task_id: uuid.UUID
    state_updates: dict[str, Any]
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    review_passed: bool = True
    error: str | None = None

@dataclass(slots=True, kw_only=True)
class BaseAgent(abc.ABC):
    """Abstract base for all CodeBot agents.

    Implements the PRA (Perception-Reasoning-Action) cognitive cycle.
    Concrete agents override perceive(), reason(), act(), and review().
    """
    agent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    agent_type: AgentType = field(init=False)  # Set by subclass
    max_iterations: int = 10
    token_budget: int = 100_000
    timeout_seconds: int = 1800  # 30 min default

    # Injected at runtime
    _state_machine: AgentStateMachine = field(init=False, repr=False)
    _metrics: AgentMetrics = field(init=False, repr=False)

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Run the full PRA cycle. Manages state transitions."""
        self._state_machine.transition(AgentStatus.INITIALIZING)
        await self._initialize(agent_input)

        self._state_machine.transition(AgentStatus.EXECUTING)
        for iteration in range(self.max_iterations):
            # PERCEIVE
            context = await self.perceive(agent_input)
            # REASON
            plan = await self.reason(context)
            # ACT
            result = await self.act(plan)
            if result.is_complete:
                break

        # REVIEW
        self._state_machine.transition(AgentStatus.REVIEWING)
        output = await self.review(result)

        if output.review_passed:
            self._state_machine.transition(AgentStatus.COMPLETED)
        else:
            self._state_machine.transition(AgentStatus.FAILED)
        return output

    @abc.abstractmethod
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Assemble context: L0/L1/L2 tiers, MCP resources, episodic memory."""
        ...

    @abc.abstractmethod
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Invoke LLM with assembled context; produce action plan."""
        ...

    @abc.abstractmethod
    async def act(self, plan: dict[str, Any]) -> Any:
        """Execute chosen action: tool calls, delegation, state updates."""
        ...

    @abc.abstractmethod
    async def review(self, result: Any) -> AgentOutput:
        """Self-review output against acceptance criteria."""
        ...

    @abc.abstractmethod
    async def _initialize(self, agent_input: AgentInput) -> None:
        """Load system prompt, tools, context. Called once per execution."""
        ...
```

### Pattern 2: Enum-Based State Machine with Transition Validation

**What:** A lightweight FSM that validates transitions, logs every state change, and emits events. No external library needed for 7 states.

**When to use:** Every BaseAgent instance has one.

**Example:**
```python
# libs/agent-sdk/src/agent_sdk/agents/state_machine.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from agent_sdk.models.enums import AgentStatus

logger = logging.getLogger(__name__)

# Valid transitions: {from_state: {to_state, ...}}
VALID_TRANSITIONS: dict[AgentStatus, set[AgentStatus]] = {
    AgentStatus.IDLE: {AgentStatus.INITIALIZING},
    AgentStatus.INITIALIZING: {AgentStatus.EXECUTING, AgentStatus.FAILED},
    AgentStatus.EXECUTING: {AgentStatus.REVIEWING, AgentStatus.FAILED},
    AgentStatus.REVIEWING: {AgentStatus.COMPLETED, AgentStatus.FAILED},
    AgentStatus.COMPLETED: set(),  # terminal
    AgentStatus.FAILED: {AgentStatus.RECOVERING},
    AgentStatus.RECOVERING: {AgentStatus.EXECUTING, AgentStatus.FAILED},
}

class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

class AgentStateMachine:
    """Manages agent lifecycle state with validated transitions."""

    def __init__(
        self,
        agent_id: str,
        on_transition: Callable[[AgentStatus, AgentStatus], None] | None = None,
    ) -> None:
        self._state = AgentStatus.IDLE
        self._agent_id = agent_id
        self._on_transition = on_transition
        self._history: list[tuple[AgentStatus, datetime]] = [
            (AgentStatus.IDLE, datetime.now(tz=timezone.utc))
        ]

    @property
    def state(self) -> AgentStatus:
        return self._state

    def transition(self, target: AgentStatus) -> None:
        if target not in VALID_TRANSITIONS.get(self._state, set()):
            raise InvalidTransitionError(
                f"Cannot transition from {self._state.value} to {target.value}"
            )
        prev = self._state
        self._state = target
        now = datetime.now(tz=timezone.utc)
        self._history.append((target, now))
        logger.info(
            "Agent %s: %s -> %s", self._agent_id, prev.value, target.value
        )
        if self._on_transition:
            self._on_transition(prev, target)
```

### Pattern 3: YAML Agent Configuration with Pydantic Validation

**What:** Pydantic models that validate YAML agent config files. One YAML file per agent type.

**When to use:** Loading agent configs at startup or hot-reload.

**Example:**
```python
# libs/agent-sdk/src/agent_sdk/models/agent_config.py
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

class RetryPolicyConfig(BaseModel):
    """Retry policy for agent recovery."""
    model_config = ConfigDict(frozen=True)

    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay_seconds: float = Field(default=2.0, gt=0)
    max_delay_seconds: float = Field(default=60.0, gt=0)
    exponential_base: float = Field(default=2.0, ge=1.0)
    recovery_strategy: str = Field(
        default="retry_with_modified_prompt",
        pattern=r"^(retry_with_modified_prompt|escalate|rollback|fallback_model)$",
    )

class ContextTiersConfig(BaseModel):
    """Token budget allocation per context tier."""
    model_config = ConfigDict(frozen=True)

    l0: int = Field(default=2000, ge=0)
    l1: int = Field(default=10000, ge=0)
    l2: int = Field(default=20000, ge=0)

class AgentConfig(BaseModel):
    """Full agent configuration loaded from YAML."""
    model_config = ConfigDict(frozen=True)

    agent_type: str
    model: str
    fallback_model: str | None = None
    provider: str = "anthropic"
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    tools: list[str] = Field(default_factory=list)
    context_tiers: ContextTiersConfig = Field(
        default_factory=ContextTiersConfig
    )
    retry_policy: RetryPolicyConfig = Field(
        default_factory=RetryPolicyConfig
    )
    timeout: int = Field(default=600, ge=1)
    system_prompt: str | None = None
    system_prompt_file: str | None = None  # relative path
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("agent_type")
    @classmethod
    def validate_agent_type(cls, v: str) -> str:
        from agent_sdk.models.enums import AgentType
        try:
            AgentType(v.upper())
        except ValueError:
            raise ValueError(f"Unknown agent type: {v}")
        return v

def load_agent_config(path: Path) -> AgentConfig:
    """Load and validate a single agent YAML config file."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    # YAML has the agent name as the top-level key
    if len(raw) == 1:
        name = next(iter(raw))
        data = raw[name]
        data.setdefault("agent_type", name.upper())
    else:
        data = raw
    return AgentConfig.model_validate(data)
```

**Example YAML config:**
```yaml
# configs/agents/orchestrator.yaml
orchestrator:
  model: claude-opus-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 8192
  temperature: 0.3
  tools:
    - graph_executor
    - task_scheduler
    - event_bus
    - checkpoint_manager
    - budget_tracker
    - approval_gate
    - agent_registry
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
    recovery_strategy: escalate
  timeout: 600
  system_prompt_file: prompts/orchestrator.md
```

### Pattern 4: Recovery Strategy (Strategy Pattern)

**What:** Composable recovery strategies that the AgentNode invokes when an agent transitions to FAILED.

**When to use:** AGNT-07 requires configurable recovery.

**Example:**
```python
# libs/agent-sdk/src/agent_sdk/agents/recovery.py
from __future__ import annotations

import abc
from dataclasses import dataclass

@dataclass(slots=True, kw_only=True)
class RecoveryContext:
    """Context passed to recovery strategies."""
    agent_id: str
    error: Exception
    attempt: int
    max_retries: int
    config: dict  # from AgentConfig.retry_policy

class RecoveryAction:
    """Result of a recovery decision."""
    RETRY = "retry"
    RETRY_MODIFIED = "retry_modified"
    ESCALATE = "escalate"
    ROLLBACK = "rollback"
    ABORT = "abort"

    def __init__(self, action: str, *, modified_prompt: str | None = None):
        self.action = action
        self.modified_prompt = modified_prompt

class RecoveryStrategy(abc.ABC):
    @abc.abstractmethod
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        ...

class RetryWithModifiedPrompt(RecoveryStrategy):
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        if ctx.attempt < ctx.max_retries:
            return RecoveryAction(
                RecoveryAction.RETRY_MODIFIED,
                modified_prompt=(
                    f"Previous attempt failed with: {ctx.error}. "
                    "Please try a different approach."
                ),
            )
        return RecoveryAction(RecoveryAction.ESCALATE)

class FallbackModelStrategy(RecoveryStrategy):
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        if ctx.attempt < ctx.max_retries:
            return RecoveryAction(RecoveryAction.RETRY)
        return RecoveryAction(RecoveryAction.ESCALATE)

class EscalateStrategy(RecoveryStrategy):
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ESCALATE)

class RollbackStrategy(RecoveryStrategy):
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ROLLBACK)
```

### Pattern 5: AgentNode Adapter for Graph Engine

**What:** Wraps a BaseAgent for execution within the graph engine's node system. Manages lifecycle, error handling, recovery, metrics recording, and event emission.

**When to use:** Every agent in the graph is wrapped in an AgentNode.

**Example:**
```python
# libs/graph-engine/src/graph_engine/nodes/agent_node.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True, kw_only=True)
class AgentNode:
    """Graph node that wraps a BaseAgent for graph execution.

    Responsibilities:
    - Convert SharedState to AgentInput
    - Run BaseAgent.execute()
    - Convert AgentOutput to SharedState updates
    - Handle recovery on failure
    - Record metrics per execution
    - Emit lifecycle events
    """
    node_id: str
    agent: Any  # BaseAgent instance (typed at runtime to avoid circular import)
    use_worktree: bool = False
    timeout_seconds: int = 1800
    recovery_strategy: Any | None = None  # RecoveryStrategy

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the wrapped agent within the graph.

        Args:
            state: SharedState dict from the graph engine.

        Returns:
            Updated SharedState dict.
        """
        agent_input = self._build_input(state)
        try:
            output = await self.agent.execute(agent_input)
            state.update(output.state_updates)
            return state
        except Exception as exc:
            if self.recovery_strategy:
                # Attempt recovery
                recovery_action = await self.recovery_strategy.decide(...)
                # Handle based on action type
                ...
            raise

    def _build_input(self, state: dict[str, Any]) -> Any:
        """Convert SharedState to AgentInput."""
        ...
```

### Anti-Patterns to Avoid

- **Giant monolithic execute():** The PRA cycle must have clear phase separation (perceive/reason/act/review). Do not merge everything into one method -- it prevents recovery from specific phases and makes testing impossible.
- **Global mutable state in agents:** Each agent execution starts with a fresh context window (Section 14.5 of SYSTEM_DESIGN). Never persist LLM conversation history across task boundaries in the agent instance.
- **State machine as strings:** Use the AgentStatus enum, not raw strings. Validate transitions. Log every transition with timestamp. This is critical for observability (AGNT-03, AGNT-12).
- **Embedding config in code:** Agent configuration (model, tools, prompts, retry policy) MUST come from YAML. Hard-coding any of these violates AGNT-05 and prevents the agent marketplace pattern planned for Phase 9.
- **Blocking I/O in agents:** All file operations, LLM calls, and event publishing must be async. The project uses `asyncio.TaskGroup` for concurrency -- blocking calls will starve other agents.
- **Tight coupling to LLM provider:** Phase 3 agents call through an LLM abstraction interface (defined here, implemented in Phase 4). Do NOT import provider-specific SDKs in agent code.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom YAML parser | PyYAML `safe_load()` + Pydantic validation | YAML edge cases (anchors, multiline strings, type coercion) are deceptively complex |
| Config validation | Manual dict checking | Pydantic BaseModel with field_validator/model_validator | Type coercion, nested validation, error messages all handled; frozen models prevent mutation |
| Event serialization | Custom JSON encoder | Pydantic `model_dump_json()` / `model_validate_json()` | Already the pattern in EventBus; consistent with agent-sdk |
| UUID generation | Custom ID schemes | `uuid.uuid4()` via stdlib | Already used in all ORM models; consistent across the project |
| Exponential backoff | Custom delay calculation | `min(base_delay * (exponential_base ** attempt), max_delay)` with jitter | Standard formula; add random jitter to prevent thundering herd |

**Key insight:** The agent framework is primarily about lifecycle orchestration and interface contracts, not complex computation. The value is in clean abstractions and validated config, not custom algorithms. Lean on Pydantic for validation, stdlib for concurrency, and the existing EventBus/ORM for persistence.

## Common Pitfalls

### Pitfall 1: Conflating Agent State Machine with ORM Agent Status
**What goes wrong:** The ORM `AgentStatus` enum (IDLE, INITIALIZING, RUNNING, WAITING, COMPLETED, FAILED, TERMINATED) differs from the AGENT_CATALOG state machine (IDLE, INITIALIZING, EXECUTING, REVIEWING, COMPLETED, FAILED, RECOVERING). If you use the ORM enum directly, you lose the REVIEWING and RECOVERING states.
**Why it happens:** Phase 1 created the ORM with a simpler status set. The detailed agent lifecycle in the catalog requires more states.
**How to avoid:** Create a runtime `AgentPhase` enum for the full state machine (with EXECUTING, REVIEWING, RECOVERING) in agent-sdk. Map to the ORM `AgentStatus` for persistence (EXECUTING/REVIEWING -> RUNNING, RECOVERING -> RUNNING). The runtime FSM has higher resolution than the database.
**Warning signs:** If the planner maps AGNT-03 states directly to the ORM enum, the REVIEWING and RECOVERING states will be missing.

### Pitfall 2: Not Stubbing LLM Provider Interface
**What goes wrong:** Phase 3 agents need to call LLMs during the Reasoning phase, but Phase 4 (Multi-LLM Abstraction) has not been built yet. If you wait for Phase 4, nothing is testable.
**Why it happens:** Sequential phase dependencies.
**How to avoid:** Define an `LLMProvider` protocol/ABC in agent-sdk with a `complete()` method. Create a `MockLLMProvider` for testing that returns canned responses. Phase 4 will implement the real providers against this interface.
**Warning signs:** If agent tests depend on real LLM calls, the test suite will be slow, flaky, and expensive.

### Pitfall 3: Overengineering the State Machine
**What goes wrong:** Using a full statechart library (python-statemachine 3.0.0 with compound states, parallel regions) for a 7-state flat FSM adds unnecessary complexity, new dependency, and learning curve.
**Why it happens:** Shiny tool syndrome.
**How to avoid:** A dict-based transition table with an enum is sufficient. The FSM is flat (no nesting), has no parallel regions, and has simple guards. If it grows beyond 15 states in the future, revisit the decision.
**Warning signs:** If the state machine implementation is more than ~80 lines of code, it is overengineered.

### Pitfall 4: Not Emitting Events on Every Transition
**What goes wrong:** The dashboard and CLI (Phase 11) rely on real-time agent status. If state transitions do not emit NATS events, there is no observability.
**Why it happens:** Event emission feels like a nice-to-have during early development.
**How to avoid:** The `AgentStateMachine.transition()` method MUST emit an `AgentEvent` via the EventBus callback. Wire this in the constructor. Test that every valid transition produces an event.
**Warning signs:** If the state machine tests do not assert event emission, this was missed.

### Pitfall 5: Mutable Agent Instances Shared Across Executions
**What goes wrong:** If a BaseAgent instance carries state from one execution to the next, you get context pollution (Section 14.5 of SYSTEM_DESIGN explicitly forbids this).
**Why it happens:** Natural OOP instinct to store intermediate results on `self`.
**How to avoid:** Agent instances should be stateless between executions. All execution state flows through `AgentInput` -> `AgentOutput`. Intermediate PRA state lives in local variables inside `execute()`, not on `self`. Use `__slots__` to prevent accidental attribute creation.
**Warning signs:** If an agent class has mutable instance attributes set during execute(), this is a bug.

### Pitfall 6: YAML Config Without Schema Validation
**What goes wrong:** Typos in YAML keys (`retr_policy` instead of `retry_policy`) silently become extra fields. Missing required fields cause runtime crashes instead of startup errors.
**Why it happens:** YAML is permissive by default.
**How to avoid:** Use Pydantic's `model_config = ConfigDict(extra="forbid")` to reject unknown keys. Use `Field(...)` with no default for truly required fields. Validate all configs at startup, not at first use.
**Warning signs:** If agent configs load without Pydantic validation, any YAML typo becomes a runtime error.

## Code Examples

Verified patterns from the project's existing codebase:

### Existing AgentEvent Pattern (agent-sdk)
```python
# libs/agent-sdk/src/agent_sdk/models/events.py (EXISTS)
class AgentEvent(BaseModel):
    agent_id: uuid.UUID
    agent_type: AgentType
    status: AgentStatus
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    payload: dict[str, Any] | None = None
```

### Existing EventBus Publishing Pattern
```python
# apps/server/src/codebot/events/bus.py (EXISTS)
async def publish_event(bus: EventBus, envelope: EventEnvelope) -> None:
    event_type_slug = envelope.event_type.value.lower().replace("_", ".")
    payload = envelope.model_dump_json().encode()
    await bus.publish(event_type_slug, payload)
```

### Existing ORM Agent Model
```python
# apps/server/src/codebot/db/models/agent.py (EXISTS)
@dataclass pattern: mapped_column for each field
# AgentType: 30 enum values
# AgentStatus: IDLE, INITIALIZING, RUNNING, WAITING, COMPLETED, FAILED, TERMINATED
# AgentExecution: tracks per-LLM-call metrics (tokens, cost, duration)
```

### YAML Config Loading Pattern (to build)
```python
# Standard pattern: yaml.safe_load -> Pydantic validation
import yaml
from pathlib import Path

def load_all_agent_configs(config_dir: Path) -> dict[str, AgentConfig]:
    """Discover and load all agent YAML configs from a directory."""
    configs: dict[str, AgentConfig] = {}
    for yaml_path in sorted(config_dir.glob("*.yaml")):
        if yaml_path.name.startswith("_"):
            continue  # skip templates/schemas
        config = load_agent_config(yaml_path)
        configs[config.agent_type] = config
    return configs
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Simple request-response agents | PRA cognitive cycle with bounded iterations | 2024-2025 (MASFactory, ReAct) | Agents reason in loops with tool use, not single-shot |
| Hard-coded agent configs | YAML-declarative config with Pydantic validation | 2025 standard | Enables agent marketplace, hot-reload, non-dev config |
| No self-review | Agents self-review before marking complete | 2025 (quality-first AI agents) | Catches hallucinations and incorrect outputs before downstream consumption |
| Flat retry (same prompt, same model) | Tiered recovery: modified prompt -> fallback model -> escalate -> rollback | 2025 (production AI agent patterns) | 70-80% of transient failures resolved; unrecoverable failures < 2% |
| Global agent state | Context window isolation per task | 2025 (context rot prevention) | Each task gets full context budget; no quality degradation from accumulated noise |

**Deprecated/outdated:**
- **Pydantic v1 validators:** Project uses Pydantic v2. Use `field_validator` and `model_validator`, not `@validator`.
- **`enum.Enum` without `str`:** Project convention is `str, enum.Enum` (StrEnum pattern) for JSON-serializable enums. The existing enums already follow this.

## Open Questions

1. **LLM Provider Interface Completeness**
   - What we know: Phase 4 builds the Multi-LLM Abstraction. Phase 3 needs a callable interface for the Reasoning phase.
   - What's unclear: Exact method signature for streaming vs. non-streaming. The SYSTEM_DESIGN shows `complete()` and `stream()` on LLMProvider.
   - Recommendation: Define a minimal `LLMProvider` protocol in agent-sdk with `async def complete(messages, model, tools) -> LLMResponse`. Create a `MockLLMProvider` for testing. Phase 4 implements the real providers.

2. **AgentStatus Enum Alignment**
   - What we know: ORM has 7 states (IDLE, INITIALIZING, RUNNING, WAITING, COMPLETED, FAILED, TERMINATED). AGENT_CATALOG specifies (IDLE, INITIALIZING, EXECUTING, REVIEWING, COMPLETED, FAILED, RECOVERING).
   - What's unclear: Whether to add EXECUTING/REVIEWING/RECOVERING to the ORM enum (requires Alembic migration) or keep a separate runtime enum.
   - Recommendation: Add an `AgentPhase` runtime enum for the full lifecycle. Map to ORM `AgentStatus` for persistence. Avoid Alembic migration in Phase 3 -- the ORM status is sufficient for database queries. The runtime phase provides higher resolution for observability.

3. **Worktree Stub Scope**
   - What we know: AGNT-04 requires isolated git worktrees. Phase 8 implements the full WorktreeManager.
   - What's unclear: How much stub infrastructure Phase 3 should build.
   - Recommendation: Define a `WorktreeProvider` protocol with `create_worktree()` and `cleanup_worktree()`. Create a `NoOpWorktreeProvider` that returns the current working directory. AgentNode accepts an optional WorktreeProvider. Phase 8 swaps in the real implementation.

4. **Tool Registry Interface**
   - What we know: Agents bind tools in `register_tools()`. Tools are defined in `apps/server/src/codebot/tools/`.
   - What's unclear: Tool registry does not exist yet. Phase 3 agents need tool binding.
   - Recommendation: Define a `ToolRegistry` protocol with `bind(agent, tool_names)` and `get_tool_schemas(agent)`. Mock it for Phase 3 tests. Concrete tools are built as needed in later phases.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.3.0 + pytest-asyncio >=0.24.0 |
| Config file | `apps/server/pyproject.toml` (tool.pytest.ini_options) |
| Quick run command | `cd apps/server && uv run pytest tests/ -x -q` |
| Full suite command | `cd apps/server && uv run pytest tests/ -v --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-01 | BaseAgent subclass runs PRA cycle (perceive, reason, act, review) | unit | `uv run pytest tests/unit/test_base_agent.py -x` | Wave 0 |
| AGNT-02 | AgentNode wraps BaseAgent, executes in graph with typed I/O | integration | `uv run pytest tests/integration/test_agent_node.py -x` | Wave 0 |
| AGNT-03 | State machine transitions valid, invalid rejected, events emitted | unit | `uv run pytest tests/unit/test_state_machine.py -x` | Wave 0 |
| AGNT-04 | Agent accepts worktree provider (stub works) | unit | `uv run pytest tests/unit/test_agent_node.py::test_worktree_stub -x` | Wave 0 |
| AGNT-05 | YAML config loads, validates, rejects invalid | unit | `uv run pytest tests/unit/test_agent_config.py -x` | Wave 0 |
| AGNT-06 | Agent self-reviews; REVIEWING state before COMPLETED | unit | `uv run pytest tests/unit/test_base_agent.py::test_review_phase -x` | Wave 0 |
| AGNT-07 | Recovery strategies triggered on FAILED; correct action returned | unit | `uv run pytest tests/unit/test_recovery.py -x` | Wave 0 |
| AGNT-12 | Metrics (execution time, tokens, cost, retries) collected and emitted | unit | `uv run pytest tests/unit/test_metrics.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/server && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd apps/server && uv run pytest tests/ -v --tb=short && cd ../../libs/agent-sdk && uv run pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_base_agent.py` -- covers AGNT-01, AGNT-06
- [ ] `tests/unit/test_state_machine.py` -- covers AGNT-03
- [ ] `tests/unit/test_agent_config.py` -- covers AGNT-05
- [ ] `tests/unit/test_recovery.py` -- covers AGNT-07
- [ ] `tests/unit/test_metrics.py` -- covers AGNT-12
- [ ] `tests/integration/test_agent_node.py` -- covers AGNT-02, AGNT-04
- [ ] Test infrastructure: MockLLMProvider, MockEventBus, MockToolRegistry fixtures in conftest.py
- [ ] libs/agent-sdk may need its own pytest config and tests directory

## Sources

### Primary (HIGH confidence)
- Project docs: `docs/design/SYSTEM_DESIGN.md` Sections 1-3, 12, 14 -- agent architecture, PRA cycle, data models, lifecycle
- Project docs: `docs/design/AGENT_CATALOG.md` -- all 30 agent specs, state machine, YAML config examples
- Project skill: `.claude/skills/codebot-agent-implementation/SKILL.md` -- full agent implementation checklist
- Project skill: `.claude/skills/codebot-graph-engine/SKILL.md` -- AgentNode, SharedState, graph patterns
- Project skill: `.claude/skills/codebot-stack-decisions/SKILL.md` -- technology versions, compatibility matrix
- Existing code: `libs/agent-sdk/src/agent_sdk/models/` -- Pydantic schemas, enums, events
- Existing code: `apps/server/src/codebot/db/models/agent.py` -- ORM Agent/AgentExecution
- Existing code: `apps/server/src/codebot/events/bus.py` -- EventBus implementation

### Secondary (MEDIUM confidence)
- [python-statemachine 3.0.0](https://pypi.org/project/python-statemachine/) -- evaluated and rejected for Phase 3 (overkill for 7-state flat FSM)
- [Pydantic YAML validation pattern](https://www.sarahglasmacher.com/how-to-validate-config-yaml-pydantic/) -- confirmed Pydantic + yaml.safe_load is the standard approach
- [LLM agent retry patterns 2025](https://sparkco.ai/blog/mastering-retry-logic-agents-a-deep-dive-into-2025-best-practices) -- four-layer fault tolerance architecture
- [Four fault tolerance patterns for AI agents](https://dev.to/klement_gunndu/4-fault-tolerance-patterns-every-ai-agent-needs-in-production-jih) -- retry, fallback, classify, checkpoint

### Tertiary (LOW confidence)
- MASFactory framework (arXiv:2603.06007) -- referenced in project docs as inspiration; PRA cycle details from project docs, not the paper directly

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, versions verified against pyproject.toml
- Architecture: HIGH -- patterns derived directly from SYSTEM_DESIGN.md and AGENT_CATALOG.md with existing code confirming conventions
- Pitfalls: HIGH -- identified from concrete gaps between ORM enums and catalog state machine, plus standard async agent patterns
- Recovery strategies: MEDIUM -- pattern well-documented in literature; specific integration with CodeBot's EventBus/SharedState needs validation during implementation

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain; project docs are the primary source of truth)
