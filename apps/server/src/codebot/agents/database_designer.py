"""DatabaseDesignerAgent -- database schema and migration designer for S3 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract architect_output, project_requirements, tech_stack
              from shared_state
- reason(): Build LLM message list with database design system prompt
- act(): Return structured database output with schema, migrations,
         ERD diagram, and indexes
- review(): Validate database_schema and migrations exist

Covers requirement ARCH-03:
  ARCH-03: Data model design with schema generation and migration planning

Note: DatabaseDesignerAgent does not have a dedicated AgentType enum value.
It uses ARCHITECT as a category fallback since it is a sub-specialization
of architecture work. It is NOT registered with @register_agent to avoid
conflicting with ArchitectAgent's registration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Database Designer agent for CodeBot, a multi-agent software
development platform. You operate in the S3 (Architecture & Design) pipeline
stage. Your purpose is to design the database schema, plan migrations,
generate ERD diagrams, and define indexing strategies.
</role>

<responsibilities>
- ARCH-03 Schema Design: Design the complete database schema including
  tables, columns, data types, constraints (primary keys, foreign keys,
  unique, check), and relationships (one-to-one, one-to-many, many-to-many).
  Apply normalization rules (3NF minimum) while considering denormalization
  for read-heavy patterns.
- Migration Planning: Generate an ordered sequence of database migrations
  that can be applied incrementally. Each migration must be reversible
  (up/down) and idempotent. Use Alembic-compatible migration format.
- ERD Generation: Produce an Entity-Relationship Diagram as structured
  JSON suitable for rendering by diagram tools. Include cardinality
  annotations and relationship labels.
- Index Strategy: Define indexes for all foreign keys, frequently queried
  columns, and composite indexes for common query patterns. Consider
  partial indexes and expression indexes where appropriate.
- Performance Considerations: Design for query performance including
  appropriate use of materialized views, partitioning strategies for
  large tables, and connection pooling recommendations.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "database_schema": object with tables (array of table objects with name,
  columns, constraints, and relationships)
- "migrations": array of migration objects with id, description,
  up_sql, down_sql, and dependencies
- "erd_diagram": structured representation with entities, relationships,
  and cardinality annotations
- "indexes": array of index objects with table, columns, type
  (btree|hash|gin|gist), and rationale
- "performance_notes": array of performance recommendations with
  table, recommendation, and impact fields
</output_format>

<constraints>
- All tables must have a primary key (prefer UUID for distributed systems)
- All foreign keys must have corresponding indexes
- Migrations must be reversible (include both up and down operations)
- Use PostgreSQL-compatible SQL syntax
- Include created_at and updated_at timestamps on all business entities
- Never store passwords in plaintext -- use bcrypt or argon2 hash columns
- Consider soft delete (deleted_at) for audit-sensitive entities
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class DatabaseDesignerAgent(BaseAgent):
    """Database schema and migration designer for S3 pipeline stage.

    Designs database schemas, plans migrations, generates ERD diagrams,
    and defines indexing strategies.

    Note: Uses ARCHITECT as agent_type fallback since there is no
    dedicated DATABASE_DESIGNER enum value. Not registered with
    @register_agent to avoid conflicting with ArchitectAgent.

    Attributes:
        agent_type: Uses ``AgentType.ARCHITECT`` as category fallback.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for schema design).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.ARCHITECT, init=False)
    name: str = "database_designer"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "schema_generator",
            "migration_generator",
            "erd_generator",
            "sql_validator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for DatabaseDesignerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract database design context from shared state.

        Pulls architect_output, project_requirements, and tech_stack
        from the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with architect_output, project_requirements, and tech_stack.
        """
        shared_state = agent_input.shared_state
        return {
            "architect_output": shared_state.get("architect_output", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
            "tech_stack": shared_state.get("tech_stack", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for database design.

        Constructs a message sequence with the system prompt and context
        from the architecture phase for the database designer role.

        Args:
            context: Dict with architect_output, project_requirements,
                     tech_stack from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Architecture output: {context.get('architect_output', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}\n\n"
                    f"Tech stack: {context.get('tech_stack', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce database design output with schema and migrations.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual LLM call is handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with database output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "database_schema": {},
                "migrations": [],
                "erd_diagram": {},
                "indexes": [],
                "performance_notes": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate database output contains required keys.

        Checks that database_schema and migrations are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            database_output.
        """
        data = result.data
        review_passed = bool(
            "database_schema" in data
            and "migrations" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"database_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Database Designer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
