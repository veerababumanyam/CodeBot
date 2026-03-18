---
name: codebot-skills-system
description: How to implement, register, execute, version, test, and share reusable agent skills in CodeBot's skill management subsystem (service.py, registry.py, executor.py, skill_creator_agent.py, skills API routes)
---

# CodeBot Agent Skill Management Subsystem

This skill covers the design and implementation of CodeBot's self-improving skill system, where agents create reusable skills that other agents consume. The skill subsystem lives in `apps/server/src/codebot/skills/` with three core modules: `service.py`, `registry.py`, and `executor.py`. The `skill_creator_agent.py` at `apps/server/src/codebot/agents/` drives skill creation. API routes are at `apps/server/src/codebot/api/routes/skills.py`.

## 1. Skill Data Model

The `Skill` entity captures everything needed to discover, version, and execute a reusable capability.

```python
# apps/server/src/codebot/skills/models.py
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


class SkillStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass(slots=True)
class Skill:
    id: uuid.UUID
    name: str
    description: str
    version: str  # semver, e.g. "1.2.0"
    created_by_agent: str  # AgentType value, e.g. "skill_creator"
    target_agents: list[str]  # AgentType values that can consume this skill
    code: str  # The executable skill body (Python source)
    status: SkillStatus = SkillStatus.DRAFT
    dependencies: list[str] = field(default_factory=list)  # skill IDs
    tags: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    output_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    usage_count: int = 0
    success_rate: Decimal = Decimal("0.0")
    project_id: uuid.UUID | None = None  # None means global / cross-project
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

### Lifecycle States

```
DRAFT --> ACTIVE --> DEPRECATED --> ARCHIVED
  |         ^            |
  +---------+            |  (can reactivate before archive)
            +------------+
```

- **DRAFT**: Skill created but not yet validated. Cannot be executed by other agents.
- **ACTIVE**: Skill passed validation and tests. Available in the registry for discovery and execution.
- **DEPRECATED**: Superseded by a newer version. Still executable but emits warnings. New consumers should use the replacement.
- **ARCHIVED**: Removed from discovery. Cannot be executed.

## 2. Skill Service Layer (`service.py`)

The service manages the full skill lifecycle: create, update, version, deprecate, archive.

### Key Patterns

```python
# apps/server/src/codebot/skills/service.py
from __future__ import annotations

from uuid import UUID

from codebot.events.bus import EventBus
from codebot.skills.models import Skill, SkillStatus
from codebot.skills.registry import SkillRegistry


class SkillService:
    """Manages skill lifecycle: create, version, deprecate, archive."""

    def __init__(self, registry: SkillRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._event_bus = event_bus

    async def create_skill(self, skill: Skill) -> Skill:
        """Validate and persist a new skill in DRAFT status."""
        self._validate_skill_definition(skill)
        skill.status = SkillStatus.DRAFT
        await self._registry.register(skill)
        await self._event_bus.publish("skill.created", {
            "skill_id": str(skill.id),
            "name": skill.name,
            "version": skill.version,
        })
        return skill

    async def activate_skill(self, skill_id: UUID) -> Skill:
        """Move a DRAFT skill to ACTIVE after tests pass."""
        skill = await self._registry.get(skill_id)
        assert skill.status == SkillStatus.DRAFT
        skill.status = SkillStatus.ACTIVE
        await self._registry.update(skill)
        return skill

    async def create_new_version(
        self, skill_id: UUID, new_version: str, code: str
    ) -> Skill:
        """Create a new version of an existing skill.

        The old version stays ACTIVE until explicitly deprecated.
        The new version starts as DRAFT.
        """
        existing = await self._registry.get(skill_id)
        # Build new skill from existing, bumping version
        new_skill = Skill(
            id=UUID(int=0),  # will be assigned by registry
            name=existing.name,
            description=existing.description,
            version=new_version,
            created_by_agent=existing.created_by_agent,
            target_agents=existing.target_agents,
            code=code,
            dependencies=existing.dependencies,
            tags=existing.tags,
            input_schema=existing.input_schema,
            output_schema=existing.output_schema,
        )
        return await self.create_skill(new_skill)

    async def deprecate_skill(
        self, skill_id: UUID, replacement_id: UUID | None = None
    ) -> None:
        """Mark a skill as DEPRECATED, optionally pointing to its replacement."""
        skill = await self._registry.get(skill_id)
        skill.status = SkillStatus.DEPRECATED
        await self._registry.update(skill)
        await self._event_bus.publish("skill.deprecated", {
            "skill_id": str(skill_id),
            "replacement_id": str(replacement_id) if replacement_id else None,
        })

    async def archive_skill(self, skill_id: UUID) -> None:
        """Remove skill from active registry. Not reversible."""
        skill = await self._registry.get(skill_id)
        skill.status = SkillStatus.ARCHIVED
        await self._registry.update(skill)

    def _validate_skill_definition(self, skill: Skill) -> None:
        """Validate skill has required fields and well-formed schemas."""
        if not skill.name or not skill.code:
            raise ValueError("Skill must have a name and code body")
        if not skill.target_agents:
            raise ValueError("Skill must declare at least one target agent")
        # Validate input/output schemas are valid JSON Schema
        # Validate version string is semver
```

### Implementation Rules

- All public methods are `async`. Use `asyncio` throughout; never block the event loop.
- Emit events on every state transition via `EventBus` so the dashboard and other agents can react.
- Validate schemas with `jsonschema` or Pydantic before persisting.
- Use strict mypy (`--strict`) and `ruff` for all skill system code.
- All dataclasses use `slots=True`.
- Python 3.12+ features are encouraged (type union syntax `X | Y`, `StrEnum`).

## 3. Skill Registry (`registry.py`)

The registry handles discovery, lookup, compatibility checking, and storage.

### Key Patterns

```python
# apps/server/src/codebot/skills/registry.py
from __future__ import annotations

from uuid import UUID

from codebot.skills.models import Skill, SkillStatus


class SkillRegistry:
    """Skill discovery, registration, lookup, and compatibility checking."""

    async def register(self, skill: Skill) -> Skill:
        """Persist a skill to the backing store. Assigns ID if not set."""
        ...

    async def get(self, skill_id: UUID) -> Skill:
        """Retrieve a skill by ID. Raises SkillNotFoundError if missing."""
        ...

    async def find_by_name(self, name: str, version: str | None = None) -> list[Skill]:
        """Find skills by name, optionally filtering to a specific version."""
        ...

    async def find_for_agent(self, agent_type: str) -> list[Skill]:
        """Return all ACTIVE skills whose target_agents includes agent_type."""
        ...

    async def search(
        self,
        query: str,
        tags: list[str] | None = None,
        agent_type: str | None = None,
    ) -> list[Skill]:
        """Full-text + tag search across the skill catalog.

        Uses the vector store for semantic search when query is natural language.
        Falls back to keyword match on name/description/tags.
        """
        ...

    async def check_compatibility(self, skill_id: UUID, agent_type: str) -> bool:
        """Check if a skill is compatible with a given agent type.

        Verifies: (1) skill is ACTIVE, (2) agent_type in target_agents,
        (3) all dependency skills are also ACTIVE.
        """
        skill = await self.get(skill_id)
        if skill.status != SkillStatus.ACTIVE:
            return False
        if agent_type not in skill.target_agents:
            return False
        for dep_id_str in skill.dependencies:
            dep = await self.get(UUID(dep_id_str))
            if dep.status != SkillStatus.ACTIVE:
                return False
        return True

    async def update(self, skill: Skill) -> Skill:
        """Persist updated skill state."""
        ...

    async def list_versions(self, name: str) -> list[Skill]:
        """Return all versions of a named skill, ordered by version descending."""
        ...

    async def get_dependency_tree(self, skill_id: UUID) -> list[Skill]:
        """Resolve the full transitive dependency tree for a skill."""
        ...
```

### Configuration (from project config)

```yaml
skill_registry:
  enabled: true
  auto_learn: true           # Skill Creator agent auto-extracts patterns
  max_skills_per_agent: 50
  skill_storage_path: "./workspace/skills"
  share_across_projects: true
```

- When `share_across_projects` is `true`, skills with `project_id = None` are discoverable globally.
- When `auto_learn` is `true`, the Skill Creator agent runs post-delivery to mine patterns.
- The registry uses the vector store (`context/vector_store.py`) for semantic skill search.

## 4. Skill Executor (`executor.py`)

The executor loads, resolves dependencies, and runs skills on behalf of an agent.

### Key Patterns

```python
# apps/server/src/codebot/skills/executor.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from codebot.skills.models import Skill
from codebot.skills.registry import SkillRegistry


@dataclass(slots=True)
class SkillResult:
    skill_id: UUID
    success: bool
    output: dict[str, Any]
    error: str | None = None
    execution_time_ms: int = 0


class SkillExecutor:
    """Executes skills on behalf of agents with dependency resolution."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        skill_id: UUID,
        agent_type: str,
        inputs: dict[str, Any],
    ) -> SkillResult:
        """Execute a skill for the calling agent.

        Steps:
        1. Check compatibility (skill is ACTIVE, agent is in target_agents).
        2. Resolve and execute dependency skills first (topological order).
        3. Validate inputs against input_schema.
        4. Execute skill code in a sandboxed environment.
        5. Validate outputs against output_schema.
        6. Update usage_count and success_rate on the skill.
        7. Emit skill.executed event.
        """
        compatible = await self._registry.check_compatibility(skill_id, agent_type)
        if not compatible:
            return SkillResult(
                skill_id=skill_id,
                success=False,
                output={},
                error=f"Skill {skill_id} not compatible with agent {agent_type}",
            )

        skill = await self._registry.get(skill_id)

        # Resolve dependencies (topological sort)
        dep_tree = await self._registry.get_dependency_tree(skill_id)
        for dep_skill in dep_tree:
            await self._run_skill_code(dep_skill, inputs)

        # Execute the skill itself
        return await self._run_skill_code(skill, inputs)

    async def _run_skill_code(
        self, skill: Skill, inputs: dict[str, Any]
    ) -> SkillResult:
        """Run skill code in a sandboxed async context.

        Uses a restricted exec environment. The skill code receives:
        - `inputs`: validated input dict
        - `context`: execution context (project info, agent state)
        Returns the skill's output dict.
        """
        ...

    async def execute_by_name(
        self,
        name: str,
        agent_type: str,
        inputs: dict[str, Any],
        version: str | None = None,
    ) -> SkillResult:
        """Convenience: look up skill by name (+ optional version) and execute."""
        skills = await self._registry.find_by_name(name, version)
        # Pick latest ACTIVE version
        active = [s for s in skills if s.status.value == "active"]
        if not active:
            return SkillResult(
                skill_id=UUID(int=0), success=False, output={},
                error=f"No active skill found: {name}",
            )
        latest = sorted(active, key=lambda s: s.version, reverse=True)[0]
        return await self.execute(latest.id, agent_type, inputs)
```

### Execution Safety

- Skill code runs in a sandboxed `exec` environment with restricted builtins.
- Network and filesystem access is limited to the project workspace.
- Execution has a configurable timeout (default 30s). Long-running skills are killed.
- Each execution updates `usage_count` and `success_rate` atomically.

## 5. Skill Creator Agent Integration

The `skill_creator_agent.py` at `apps/server/src/codebot/agents/` is the agent that mines patterns and creates skills. It runs in Stage S9 (Documentation & Knowledge) in internal parallel with Hooks Creator and Tools Creator.

### Agent Profile

| Property | Value |
|----------|-------|
| Role | Creates reusable skills from observed code patterns |
| Category | Tooling |
| Graph Position | Cross-cutting; post-delivery pattern extraction |
| Model | Claude Opus 4 (pattern identification), Claude Sonnet 4 (extraction), Claude Haiku 3.5 (docs) |
| Upstream | All Implementation agents, Orchestrator |
| Downstream | All agents (via skill library), Orchestrator (registry) |

### Agent State Machine

```
IDLE --> INITIALIZING --> ANALYZING --> EXTRACTING --> PACKAGING --> TESTING --> COMPLETED
                            |              |             |            |
                            v              v             v            v
                          FAILED        FAILED        FAILED       FAILED
```

### How the Agent Creates Skills

1. **Analyze** completed project code and pipeline execution logs for recurring patterns (auth flows, CRUD, deployment configs, form validation, API clients).
2. **Extract** patterns into parameterized skill definitions using AST analysis + LLM.
3. **Package** each skill with `input_schema`, `output_schema`, documentation, and test cases.
4. **Register** the skill via `SkillService.create_skill()` in DRAFT status.
5. **Test** the skill against synthetic inputs using `skill_tester` tool.
6. **Activate** the skill via `SkillService.activate_skill()` if tests pass.

### Agent Tools

| Tool | Purpose |
|------|---------|
| `pattern_extractor` | Identify reusable patterns from code via AST + LLM |
| `skill_packager` | Package patterns into skill definitions |
| `skill_registry` | Register and version skills in library |
| `skill_tester` | Validate skill correctness with test cases |
| `skill_documenter` | Generate skill documentation with examples |

### Example: Agent Creating a Skill

```python
# Inside skill_creator_agent.py execute() method
async def _create_skill_from_pattern(self, pattern: ExtractedPattern) -> Skill:
    skill = Skill(
        id=uuid4(),
        name=pattern.name,
        description=pattern.description,
        version="1.0.0",
        created_by_agent="skill_creator",
        target_agents=pattern.applicable_agents,
        code=pattern.parameterized_code,
        input_schema=pattern.input_schema,
        output_schema=pattern.output_schema,
        tags=pattern.tags,
    )
    created = await self.skill_service.create_skill(skill)

    # Run tests
    test_results = await self.skill_tester.run(created.id, pattern.test_cases)
    if test_results.all_passed:
        await self.skill_service.activate_skill(created.id)

    return created
```

## 6. API Endpoints

Skill management is exposed via REST at `apps/server/src/codebot/api/routes/skills.py`.

### Routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/skills` | Create a new skill (DRAFT) |
| `GET` | `/api/v1/skills` | List skills with filtering (status, agent, tags, search query) |
| `GET` | `/api/v1/skills/{skill_id}` | Get skill by ID |
| `PUT` | `/api/v1/skills/{skill_id}` | Update skill metadata or code |
| `POST` | `/api/v1/skills/{skill_id}/activate` | Move skill from DRAFT to ACTIVE |
| `POST` | `/api/v1/skills/{skill_id}/deprecate` | Deprecate a skill, optionally set replacement |
| `POST` | `/api/v1/skills/{skill_id}/archive` | Archive a skill |
| `POST` | `/api/v1/skills/{skill_id}/execute` | Execute a skill with given inputs |
| `GET` | `/api/v1/skills/{skill_id}/versions` | List all versions of a skill |
| `POST` | `/api/v1/skills/{skill_id}/versions` | Create a new version |
| `GET` | `/api/v1/skills/{skill_id}/dependencies` | Get dependency tree |
| `GET` | `/api/v1/skills/search` | Semantic + keyword search |

### Request/Response Schemas

Define Pydantic models in `apps/server/src/codebot/api/schemas/`:

```python
from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    target_agents: list[str]
    code: str
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)


class SkillExecuteRequest(BaseModel):
    agent_type: str
    inputs: dict


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    status: str
    created_by_agent: str
    target_agents: list[str]
    usage_count: int
    success_rate: float
    tags: list[str]
    created_at: str
    updated_at: str
```

## 7. Skill Testing and Validation

Every skill must pass validation before activation.

### Validation Checklist

1. **Schema validation**: `input_schema` and `output_schema` are valid JSON Schema drafts.
2. **Code safety**: Skill code passes static analysis (no dangerous imports, no filesystem escape, no network calls outside allowed list).
3. **Execution test**: Skill executes successfully with at least one set of synthetic inputs.
4. **Output conformance**: Skill output matches `output_schema`.
5. **Dependency check**: All declared dependencies are ACTIVE in the registry.
6. **Idempotency**: Skill produces the same output for the same input (where applicable).

### Writing Skill Tests

```python
# apps/server/tests/unit/skills/test_my_skill.py
import pytest
from codebot.skills.executor import SkillExecutor
from codebot.skills.registry import SkillRegistry


@pytest.fixture
async def executor(skill_registry: SkillRegistry) -> SkillExecutor:
    return SkillExecutor(registry=skill_registry)


async def test_skill_executes_with_valid_inputs(executor: SkillExecutor) -> None:
    result = await executor.execute_by_name(
        name="react-form-validator",
        agent_type="frontend_dev",
        inputs={"fields": [{"name": "email", "type": "email", "required": True}]},
    )
    assert result.success
    assert "validation_code" in result.output


async def test_skill_rejects_incompatible_agent(executor: SkillExecutor) -> None:
    result = await executor.execute_by_name(
        name="react-form-validator",
        agent_type="infra_engineer",  # not in target_agents
        inputs={"fields": []},
    )
    assert not result.success
    assert "not compatible" in (result.error or "")


async def test_skill_dependency_resolution(executor: SkillExecutor) -> None:
    """Skills with dependencies should execute deps first."""
    result = await executor.execute_by_name(
        name="crud-with-auth",
        agent_type="backend_dev",
        inputs={"model_name": "User"},
    )
    assert result.success
```

### Test commands

```bash
# Run skill system unit tests
pytest apps/server/tests/unit/skills/ -v --strict-markers

# Run with coverage
pytest apps/server/tests/unit/skills/ --cov=codebot.skills --cov-report=term-missing

# Type check the skills module
mypy apps/server/src/codebot/skills/ --strict
```

## 8. Cross-Project Skill Sharing

Skills become truly powerful when shared across projects.

### How Sharing Works

- Skills with `project_id = None` are **global** and visible to all projects.
- Skills with a specific `project_id` are **project-scoped** and only visible within that project.
- The Skill Creator agent defaults to creating global skills when `skill_registry.share_across_projects` is `true` in config.
- When an agent in project B discovers a useful skill from project A, the registry returns it as long as it is global and ACTIVE.

### Versioning Strategy

- Use semver (`MAJOR.MINOR.PATCH`).
- MAJOR bump: breaking change to input/output schema.
- MINOR bump: new optional inputs or capabilities, backward-compatible.
- PATCH bump: bug fix, no schema change.
- Multiple versions of the same skill can be ACTIVE simultaneously. The executor picks the latest ACTIVE version by default. Consumers can pin to a specific version.

### Skill Dependency Management

- Skills declare dependencies by skill ID in the `dependencies` field.
- The registry resolves the full transitive dependency tree before execution.
- Circular dependencies are rejected at registration time.
- If a dependency is deprecated, a warning is emitted but execution proceeds. If archived, execution fails with a clear error.

## Event Contracts

Skill system events emitted on the EventBus:

| Event | Payload | When |
|-------|---------|------|
| `skill.created` | `{skill_id, name, version, created_by_agent}` | New skill registered |
| `skill.activated` | `{skill_id, name, version}` | Skill moved to ACTIVE |
| `skill.deprecated` | `{skill_id, replacement_id}` | Skill deprecated |
| `skill.executed` | `{skill_id, name, executed_by_agent, project_id, success, execution_time_ms}` | Skill executed |

## Quick Reference: File Map

| File | Purpose |
|------|---------|
| `apps/server/src/codebot/skills/__init__.py` | Package init |
| `apps/server/src/codebot/skills/service.py` | Skill lifecycle (create, version, deprecate, archive) |
| `apps/server/src/codebot/skills/registry.py` | Discovery, lookup, compatibility, storage |
| `apps/server/src/codebot/skills/executor.py` | Execution engine with dependency resolution |
| `apps/server/src/codebot/agents/skill_creator_agent.py` | Agent that mines patterns and creates skills |
| `apps/server/src/codebot/api/routes/skills.py` | REST API endpoints |
| `apps/server/tests/unit/skills/` | Unit tests |
| `apps/server/tests/integration/skills/` | Integration tests |
| `configs/skills/` | Built-in skill definitions (YAML) |
| `workspace/skills/` | Runtime skill storage |
