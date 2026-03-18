---
name: CodeBot Hooks System
description: >
  Working with CodeBot's lifecycle hooks subsystem — registration, execution,
  event-bus integration, and the hooks creator agent.
tags:
  - codebot
  - hooks
  - lifecycle
  - events
  - pipeline
globs:
  - "apps/server/src/codebot/hooks/**"
  - "apps/server/src/codebot/events/**"
  - "apps/server/src/codebot/agents/hooks_creator_agent.py"
  - "apps/server/src/codebot/api/routes/hooks.py"
---

# CodeBot Hooks System

## Overview

The hooks subsystem lets agents and the pipeline execute actions at specific
lifecycle points. Hooks are created during Stage S9 (Documentation & Knowledge)
by the `hooks_creator_agent` and fire in response to events emitted by the
event bus.

### Key paths

| Purpose | Path |
|---|---|
| Hook lifecycle management | `apps/server/src/codebot/hooks/service.py` |
| Hook registration & lookup | `apps/server/src/codebot/hooks/registry.py` |
| Hook execution engine | `apps/server/src/codebot/hooks/executor.py` |
| Hooks creator agent | `apps/server/src/codebot/agents/hooks_creator_agent.py` |
| Event bus | `apps/server/src/codebot/events/bus.py` |
| Event type definitions | `apps/server/src/codebot/events/types.py` |
| Event persistence | `apps/server/src/codebot/events/store.py` |
| Event handlers | `apps/server/src/codebot/events/handlers.py` |
| Hooks API routes | `apps/server/src/codebot/api/routes/hooks.py` |

### Tech constraints

- Python 3.12+
- Strict mypy (no implicit Any)
- Formatting/linting via ruff
- Async-first (`async def` everywhere)
- Dataclasses use `slots=True`

---

## 1. Hook Data Model and Lifecycle

A hook is a dataclass that binds a callable to a lifecycle event.

```python
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
import uuid

class HookStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"

class HookType(StrEnum):
    PRE_PHASE = "pre_phase"
    POST_PHASE = "post_phase"
    PRE_AGENT = "pre_agent"
    POST_AGENT = "post_agent"
    ON_ERROR = "on_error"
    ON_APPROVAL = "on_approval"
    ON_EVENT = "on_event"

@dataclass(slots=True)
class Hook:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    hook_type: HookType = HookType.ON_EVENT
    target: str = ""          # event name or phase/agent identifier
    priority: int = 100       # lower = earlier execution
    timeout_ms: int = 5000
    enabled: bool = True
    status: HookStatus = HookStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Lifecycle states

```
PENDING  -->  ACTIVE  -->  DISABLED
                |
                v
             FAILED
```

- **PENDING**: Registered but not yet validated by the service.
- **ACTIVE**: Validated and eligible for execution.
- **DISABLED**: Manually or automatically turned off.
- **FAILED**: Exceeded error threshold; requires manual re-enable.

---

## 2. Hook Types

| Type | Fires when | Typical use |
|---|---|---|
| `PRE_PHASE` | Before a pipeline phase begins | Gate checks, config injection |
| `POST_PHASE` | After a pipeline phase completes | Metrics, artifact validation |
| `PRE_AGENT` | Before an agent starts work | Context enrichment, logging |
| `POST_AGENT` | After an agent completes | Result post-processing |
| `ON_ERROR` | An agent or phase raises an error | Alerting, fallback logic |
| `ON_APPROVAL` | `HumanApprovalRequired` event fires | Notification dispatch |
| `ON_EVENT` | Any named event on the bus | General-purpose extensibility |

When creating a hook, set `hook_type` and `target` together. For phase/agent
types, `target` is the phase or agent identifier string. For `ON_EVENT`,
`target` is the event type name (e.g. `"AgentCompleted"`).

---

## 3. Hook Registry Patterns

The registry (`registry.py`) is the single source of truth for all registered
hooks.

### Registration

```python
registry = HookRegistry()
await registry.register(hook)
```

- Validates uniqueness of `hook.id`.
- Sets status to `ACTIVE` if validation passes.
- Raises `DuplicateHookError` on collision.

### Lookup

```python
# All hooks for a given type and target, sorted by priority
hooks = await registry.lookup(hook_type=HookType.PRE_AGENT, target="planner_agent")

# Single hook by ID
hook = await registry.get(hook_id)
```

### Priority ordering

Hooks execute in ascending `priority` order (lower number = higher priority).
Hooks with equal priority execute in registration order. Convention:

| Range | Purpose |
|---|---|
| 0-49 | System / framework hooks |
| 50-99 | Platform-level hooks |
| 100-199 | User-defined hooks (default 100) |
| 200+ | Logging / telemetry hooks |

### Deregistration

```python
await registry.deregister(hook_id)
```

Removes the hook and cancels any pending executions in the executor.

---

## 4. Hook Executor

The executor (`executor.py`) is responsible for invoking hooks with proper
timeout handling and error isolation.

### Invocation flow

```
1. Executor receives event + list of matching hooks (from registry lookup)
2. For each hook (in priority order):
   a. Wrap callable in asyncio.wait_for with hook.timeout_ms
   b. Invoke the callable, passing the event context
   c. Capture result or exception
3. Return aggregated HookExecutionResult
```

### Timeout handling

```python
async def _execute_single(self, hook: Hook, context: EventContext) -> HookResult:
    try:
        result = await asyncio.wait_for(
            hook.callable(context),
            timeout=hook.timeout_ms / 1000,
        )
        return HookResult(hook_id=hook.id, success=True, value=result)
    except asyncio.TimeoutError:
        return HookResult(hook_id=hook.id, success=False, error="timeout")
```

### Error isolation

- A failing hook never blocks subsequent hooks in the chain.
- Errors are captured per-hook and returned in the aggregated result.
- If a hook fails more than `max_failures` times (configurable, default 3),
  the service transitions it to `FAILED` status and deregisters it.
- `ON_ERROR` hooks have their own isolated execution path to prevent
  infinite error loops.

### Concurrency

- By default, hooks of the same type execute **sequentially** in priority
  order to maintain deterministic behavior.
- Set `parallel=True` on the executor call to run independent hooks
  concurrently (useful for logging/telemetry hooks).

---

## 5. Event Bus Integration

Hooks are powered by the event system at `apps/server/src/codebot/events/`.

### Core event types

Defined in `events/types.py`:

```python
class EventType(StrEnum):
    AGENT_STARTED = "AgentStarted"
    AGENT_COMPLETED = "AgentCompleted"
    AGENT_FAILED = "AgentFailed"
    PHASE_STARTED = "PhaseStarted"
    PHASE_COMPLETED = "PhaseCompleted"
    HUMAN_APPROVAL_REQUIRED = "HumanApprovalRequired"
    HOOK_REGISTERED = "HookRegistered"
    HOOK_EXECUTED = "HookExecuted"
    PIPELINE_STARTED = "PipelineStarted"
    PIPELINE_COMPLETED = "PipelineCompleted"
```

### Subscribing to events

The hook service subscribes to the event bus on startup and routes events
to the executor:

```python
class HookService:
    async def start(self) -> None:
        self._bus = EventBus()
        self._bus.subscribe("*", self._on_event)  # wildcard subscription

    async def _on_event(self, event: Event) -> None:
        hooks = await self._registry.lookup_by_event(event.event_type)
        if hooks:
            await self._executor.execute(hooks, event.context)
```

### Emitting events from hooks

Hooks can themselves emit events, enabling chaining:

```python
async def my_hook(context: EventContext) -> None:
    # Do work...
    await context.bus.emit(Event(
        event_type=EventType.HOOK_EXECUTED,
        payload={"hook_name": "my_hook", "result": "ok"},
    ))
```

Guard against cycles: the executor tracks the current execution chain depth
and raises `HookRecursionError` if it exceeds `max_depth` (default 5).

### Event store

`events/store.py` persists events for replay and audit. The hook service
reads from the store when replaying hooks after a restart.

---

## 6. Hooks Creator Agent Integration

The `hooks_creator_agent.py` at `apps/server/src/codebot/agents/` is a
specialized agent that runs during Stage S9 (Documentation & Knowledge).

### What it does

1. Analyzes the project context and pipeline configuration.
2. Proposes a set of lifecycle hooks tailored to the project.
3. Generates hook implementations as async callables.
4. Registers them via the `HookService`.

### Interacting with it

The agent exposes its output as a list of `HookDefinition` objects:

```python
@dataclass(slots=True)
class HookDefinition:
    name: str
    hook_type: HookType
    target: str
    priority: int
    description: str
    implementation: str  # source code of the async callable
```

### Extending the agent

To add a new hook-generation strategy:

1. Add a method to the agent class that returns `list[HookDefinition]`.
2. Register the strategy in the agent's `_strategies` list.
3. The agent iterates strategies and merges results, deduplicating by name.

---

## 7. API Endpoints for Hook Management

Routes live at `apps/server/src/codebot/api/routes/hooks.py`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/hooks` | List all hooks (supports `?type=` and `?status=` filters) |
| `GET` | `/api/hooks/{hook_id}` | Get a single hook by ID |
| `POST` | `/api/hooks` | Register a new hook |
| `PATCH` | `/api/hooks/{hook_id}` | Update hook fields (priority, enabled, timeout) |
| `DELETE` | `/api/hooks/{hook_id}` | Deregister a hook |
| `POST` | `/api/hooks/{hook_id}/enable` | Re-enable a disabled/failed hook |
| `POST` | `/api/hooks/{hook_id}/disable` | Disable a hook without removing it |
| `GET` | `/api/hooks/{hook_id}/executions` | Execution history for a hook |

### Request/response patterns

All endpoints return JSON. POST/PATCH accept JSON bodies. Standard error
shape:

```json
{
  "error": {
    "code": "HOOK_NOT_FOUND",
    "message": "No hook with id abc-123"
  }
}
```

Use `async` route handlers that delegate to `HookService` methods.

---

## 8. Testing Hooks in Isolation

### Unit testing a hook callable

```python
import pytest
from unittest.mock import AsyncMock

from codebot.hooks.executor import HookExecutor
from codebot.events.types import EventContext

@pytest.mark.asyncio
async def test_my_hook_runs_successfully() -> None:
    context = EventContext(
        event_type="AgentCompleted",
        payload={"agent": "planner_agent"},
        bus=AsyncMock(),
    )
    result = await my_hook(context)
    assert result is not None
```

### Testing registration and lookup

```python
@pytest.mark.asyncio
async def test_registry_lookup_by_type() -> None:
    registry = HookRegistry()
    hook = Hook(name="test", hook_type=HookType.PRE_AGENT, target="planner_agent")
    await registry.register(hook)

    found = await registry.lookup(HookType.PRE_AGENT, target="planner_agent")
    assert len(found) == 1
    assert found[0].id == hook.id
```

### Testing executor timeout and error isolation

```python
@pytest.mark.asyncio
async def test_executor_isolates_failing_hook() -> None:
    executor = HookExecutor()

    async def bad_hook(ctx: EventContext) -> None:
        raise RuntimeError("boom")

    async def good_hook(ctx: EventContext) -> str:
        return "ok"

    hooks = [
        Hook(name="bad", hook_type=HookType.ON_EVENT, target="*", priority=1),
        Hook(name="good", hook_type=HookType.ON_EVENT, target="*", priority=2),
    ]
    # Attach callables (implementation detail depends on your binding approach)
    hooks[0].callable = bad_hook  # type: ignore[attr-defined]
    hooks[1].callable = good_hook  # type: ignore[attr-defined]

    results = await executor.execute(hooks, EventContext(...))
    assert not results[0].success
    assert results[1].success
    assert results[1].value == "ok"
```

### Testing event bus integration

```python
@pytest.mark.asyncio
async def test_hook_receives_event_from_bus() -> None:
    bus = EventBus()
    service = HookService(bus=bus)
    await service.start()

    received: list[EventContext] = []

    async def capture_hook(ctx: EventContext) -> None:
        received.append(ctx)

    hook = Hook(
        name="capture",
        hook_type=HookType.ON_EVENT,
        target="AgentCompleted",
    )
    hook.callable = capture_hook  # type: ignore[attr-defined]
    await service.register(hook)

    await bus.emit(Event(
        event_type=EventType.AGENT_COMPLETED,
        payload={"agent": "planner_agent"},
    ))

    assert len(received) == 1
    assert received[0].payload["agent"] == "planner_agent"
```

### Tips

- Always use `pytest.mark.asyncio` for async test functions.
- Mock the `EventBus` when testing hooks in isolation to avoid side effects.
- Use `asyncio.timeout` (Python 3.11+) or `asyncio.wait_for` to assert that
  hooks respect their configured timeouts.
- Run `mypy --strict` and `ruff check` before committing hook code.

---

## Quick Reference: Adding a New Hook

1. Define the hook callable as an `async def` accepting `EventContext`.
2. Create a `Hook` dataclass instance with the desired type, target, and priority.
3. Register it via `HookService.register(hook)` or POST to `/api/hooks`.
4. Verify with a unit test that the hook fires for the expected event.
5. Check execution history via `GET /api/hooks/{id}/executions`.
