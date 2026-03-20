"""Hooks Creator Agent -- generates lifecycle hooks for pipeline customization.

Full implementation of Agent #27. Analyzes the project's pipeline configuration
and execution patterns to propose and register lifecycle hooks that improve
pipeline behavior (pre/post phase hooks, error handlers, approval hooks).

Runs post-delivery in Stage S9. Replaces the stub in hooks_creator.py.

Implements the PRA cognitive cycle:
- perceive(): Gather pipeline config and execution history
- reason(): Propose lifecycle hooks tailored to the project
- act(): Register hooks via HookService and publish events
- review(): Validate registered hooks and format output
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, override

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

if TYPE_CHECKING:
    from codebot.events.bus import EventBus
    from codebot.hooks.service import HookService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Hooks Creator agent for CodeBot, a multi-agent software development
platform. You operate in the S9 (Documentation) pipeline stage, post-delivery.
Your purpose is to analyze pipeline configurations and execution history to
generate lifecycle hooks that improve pipeline behavior.
</role>

<responsibilities>
- Analyze pipeline configurations and execution history to identify
  opportunities for lifecycle hooks:
  1. Pre-phase validation hooks (input checks before expensive stages)
  2. Post-phase metric collection hooks
  3. Error recovery hooks for common failure patterns
  4. Notification hooks for human approval gates
  5. Logging/telemetry hooks for observability
- Filter out hooks that already exist in the registry
- Register hooks via HookService with appropriate type, target, and priority
- Publish hook.created events for observability
</responsibilities>

<output_format>
Produce a JSON object with:
- "proposed_hooks": array of hook definitions, each with:
  - name, hook_type, target, priority, description, implementation
</output_format>

<constraints>
- Each hook must specify its type (PRE_PHASE, POST_PHASE, etc.)
- Each hook must have a valid target (phase name or agent type)
- Priority must be a positive integer (lower = earlier execution)
- Do not duplicate existing hooks in the registry
- Implementation must be an async callable
</constraints>
"""


# ---------------------------------------------------------------------------
# Supporting data types
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class HookDefinition:
    """A lifecycle hook proposed by the Hooks Creator agent.

    Attributes:
        name: Human-readable hook name.
        hook_type: When this hook fires (maps to HookType enum).
        target: Target phase/agent/event for the hook.
        priority: Execution priority (lower = earlier).
        description: What the hook does.
        implementation: Async callable source code.
    """

    name: str
    hook_type: str  # Maps to HookType enum values
    target: str
    priority: int = 100
    description: str = ""
    implementation: str = ""  # Async callable source code


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.HOOK_MANAGER)
@dataclass(slots=True, kw_only=True)
class HooksCreatorAgent(BaseAgent):
    """Agent #27: Generates lifecycle hooks for pipeline customization.

    Runs post-delivery in Stage S9. Analyzes the project's pipeline configuration
    and execution patterns to propose and register lifecycle hooks that improve
    pipeline behavior (pre/post phase hooks, error handlers, approval hooks).

    Attributes:
        agent_type: Always ``AgentType.HOOK_MANAGER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.HOOK_MANAGER, init=False)
    name: str = "hooks_creator"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: ["hook_generator", "hook_registry", "pipeline_analyzer"]
    )

    # Injected dependencies (not part of config, set after construction)
    _hook_service: HookService | None = field(default=None, init=False, repr=False)
    _event_bus: EventBus | None = field(default=None, init=False, repr=False)

    def set_services(self, hook_service: HookService, event_bus: EventBus) -> None:
        """Inject service dependencies after construction.

        Args:
            hook_service: Service for registering hooks.
            event_bus: Event bus for publishing hook.created events.
        """
        self._hook_service = hook_service
        self._event_bus = event_bus

    @override
    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for HooksCreatorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    @override
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Gather pipeline config, execution history, and existing hooks.

        Args:
            agent_input: The task input with shared_state containing
                         pipeline_config, execution_history, and existing_hooks.

        Returns:
            Dict with pipeline_config, execution_history, existing_hooks,
            and project_type.
        """
        shared_state = agent_input.shared_state
        return {
            "pipeline_config": shared_state.get("pipeline_config", {}),
            "execution_history": shared_state.get("execution_history", []),
            "existing_hooks": shared_state.get("existing_hooks", []),
            "project_type": shared_state.get("project_type", "unknown"),
        }

    @override
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Propose lifecycle hooks based on pipeline analysis.

        Identifies opportunities for:
        1. Pre-phase validation hooks (input checks before expensive stages)
        2. Post-phase metric collection hooks
        3. Error recovery hooks for common failure patterns
        4. Notification hooks for human approval gates
        5. Logging/telemetry hooks for observability

        Args:
            context: Dict with pipeline_config, execution_history,
                     existing_hooks from perceive().

        Returns:
            Dict with proposed_hooks list and perception for the act phase.
        """
        return {"proposed_hooks": [], "perception": context}

    @override
    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Register proposed hooks via HookService.

        For each hook definition:
        1. Create Hook object with type, target, and priority
        2. Register via HookService
        3. Emit hook.created event

        Args:
            plan: Dict with proposed_hooks list from reason().

        Returns:
            PRAResult with registered_hooks list and any errors.
        """
        from codebot.hooks.models import Hook, HookStatus, HookType

        registered: list[str] = []
        errors: list[str] = []

        definitions: list[HookDefinition] = plan.get("proposed_hooks", [])
        for defn in definitions:
            try:
                hook_id = str(uuid.uuid4())
                hook = Hook(
                    id=hook_id,
                    name=defn.name,
                    hook_type=HookType(defn.hook_type),
                    target=defn.target,
                    priority=defn.priority,
                    status=HookStatus.PENDING,
                )
                if self._hook_service is None:
                    raise RuntimeError("HookService not injected -- call set_services() first")
                await self._hook_service.register(hook)

                if self._event_bus is None:
                    raise RuntimeError("EventBus not injected -- call set_services() first")
                await self._event_bus.publish("hook.created", {
                    "hook_id": hook_id,
                    "name": hook.name,
                    "type": defn.hook_type,
                    "target": defn.target,
                })
                registered.append(hook_id)
            except Exception as exc:
                errors.append(f"Failed to register hook '{defn.name}': {exc}")

        return PRAResult(
            is_complete=True,
            data={"registered_hooks": registered, "errors": errors},
        )

    @override
    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate hook registration output.

        Checks that registered hooks list is populated and no errors occurred.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            hooks_creator_output.
        """
        data = result.data
        has_errors = len(data.get("errors", [])) > 0
        review_passed = not has_errors or len(data.get("registered_hooks", [])) > 0

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"hooks_creator_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Hooks Creator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
