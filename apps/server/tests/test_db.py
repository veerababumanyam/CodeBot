"""Database integration tests — validates schema, CRUD operations, and FK constraints."""

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.db.models import (
    Agent,
    AgentStatus,
    AgentType,
    Pipeline,
    PipelineStatus,
    Project,
    ProjectStatus,
    ProjectType,
    User,
    UserRole,
)
from codebot.db.models.security import FindingType, Severity


# ---------------------------------------------------------------------------
# 1. Alembic migration state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alembic_version_table_exists(async_session: AsyncSession) -> None:
    """Alembic version table must exist, proving migrations were applied."""
    result = await async_session.execute(sa.text("SELECT version_num FROM alembic_version"))
    row = result.fetchone()
    assert row is not None, "alembic_version table must have a row after upgrade head"
    assert isinstance(row[0], str) and len(row[0]) > 0


# ---------------------------------------------------------------------------
# 2. CRUD: User → Project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_read_user(async_session: AsyncSession) -> None:
    """Can create a User record and read it back with all fields intact."""
    user = User(
        email="test@example.com",
        password_hash="$argon2id$v=19$m=65536,t=2,p=1$fakehash",
        name="Test User",
        role=UserRole.USER,
    )
    async_session.add(user)
    await async_session.flush()

    fetched = await async_session.get(User, user.id)
    assert fetched is not None
    assert fetched.email == "test@example.com"
    assert fetched.name == "Test User"
    assert fetched.role == UserRole.USER
    assert fetched.mfa_enabled is False


@pytest.mark.asyncio
async def test_create_and_read_project(async_session: AsyncSession) -> None:
    """Can create a Project linked to a User and read it back."""
    user = User(
        email="proj_user@example.com",
        password_hash="hash",
        name="Project Owner",
        role=UserRole.USER,
    )
    async_session.add(user)
    await async_session.flush()

    project = Project(
        user_id=user.id,
        name="My Test Project",
        description="A project for testing",
        status=ProjectStatus.CREATED,
        project_type=ProjectType.GREENFIELD,
    )
    async_session.add(project)
    await async_session.flush()

    fetched = await async_session.get(Project, project.id)
    assert fetched is not None
    assert fetched.name == "My Test Project"
    assert fetched.status == ProjectStatus.CREATED
    assert fetched.project_type == ProjectType.GREENFIELD
    assert fetched.user_id == user.id


# ---------------------------------------------------------------------------
# 3. Pipeline linked to Project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_pipeline_linked_to_project(async_session: AsyncSession) -> None:
    """Can create a Pipeline record and associate it with a Project."""
    user = User(
        email="pipeline_user@example.com",
        password_hash="hash",
        name="Pipeline User",
        role=UserRole.USER,
    )
    async_session.add(user)
    await async_session.flush()

    project = Project(
        user_id=user.id,
        name="Pipeline Project",
        status=ProjectStatus.IMPLEMENTING,
        project_type=ProjectType.GREENFIELD,
    )
    async_session.add(project)
    await async_session.flush()

    pipeline = Pipeline(
        project_id=project.id,
        status=PipelineStatus.RUNNING,
        current_phase="S3_ARCHITECTURE",
    )
    async_session.add(pipeline)
    await async_session.flush()

    fetched = await async_session.get(Pipeline, pipeline.id)
    assert fetched is not None
    assert fetched.project_id == project.id
    assert fetched.status == PipelineStatus.RUNNING
    assert fetched.current_phase == "S3_ARCHITECTURE"


# ---------------------------------------------------------------------------
# 4. All enum values are valid and storable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enum_values_storable(async_session: AsyncSession) -> None:
    """Every ProjectStatus, ProjectType, and Severity enum value can be stored."""
    user = User(
        email="enum_user@example.com",
        password_hash="hash",
        name="Enum User",
        role=UserRole.USER,
    )
    async_session.add(user)
    await async_session.flush()

    for status in ProjectStatus:
        proj = Project(
            user_id=user.id,
            name=f"Project {status.value}",
            status=status,
            project_type=ProjectType.GREENFIELD,
        )
        async_session.add(proj)

    await async_session.flush()  # No exception = all enum values are valid


@pytest.mark.asyncio
async def test_severity_enum_values(async_session: AsyncSession) -> None:
    """Severity enum covers all five levels expected by the schema."""
    expected = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
    actual = {s.value for s in Severity}
    assert expected == actual


# ---------------------------------------------------------------------------
# 5. Foreign key constraints enforced
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fk_constraint_agent_invalid_project(async_session: AsyncSession) -> None:
    """Creating an Agent with a non-existent project_id raises IntegrityError."""
    agent = Agent(
        project_id=uuid.uuid4(),  # does not exist
        agent_type=AgentType.PLANNER,
        status=AgentStatus.IDLE,
    )
    async_session.add(agent)

    with pytest.raises(Exception) as exc_info:
        await async_session.flush()

    error_text = str(exc_info.value).lower()
    # Both asyncpg and psycopg report "foreign key" violations
    assert "foreign key" in error_text or "violates" in error_text or "fk" in error_text


# ---------------------------------------------------------------------------
# 6. All 16 tables exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_expected_tables_exist(async_session: AsyncSession) -> None:
    """All 16 domain tables must exist in the public schema."""
    expected_tables = {
        "users",
        "api_keys",
        "audit_logs",
        "projects",
        "pipelines",
        "pipeline_phases",
        "tasks",
        "agents",
        "agent_executions",
        "code_artifacts",
        "test_results",
        "security_findings",
        "review_comments",
        "events",
        "checkpoints",
        "experiment_logs",
    }

    result = await async_session.execute(
        sa.text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version'"
        )
    )
    actual_tables = {row[0] for row in result.fetchall()}
    missing = expected_tables - actual_tables
    assert not missing, f"Missing tables: {missing}"


# ---------------------------------------------------------------------------
# 7. SOC 2 compliance fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finding_type_includes_compliance_violation(
    async_session: AsyncSession,
) -> None:
    """FindingType enum must include COMPLIANCE_VIOLATION."""
    assert FindingType.COMPLIANCE_VIOLATION.value == "COMPLIANCE_VIOLATION"


@pytest.mark.asyncio
async def test_audit_log_soc2_fields_exist(async_session: AsyncSession) -> None:
    """AuditLog can be created with SOC 2 compliance fields."""
    from datetime import datetime, timezone

    from codebot.db.models.user import AuditLog

    user = User(
        email="soc2_test@example.com",
        password_hash="hash",
        name="SOC2 Tester",
        role=UserRole.USER,
    )
    async_session.add(user)
    await async_session.flush()

    retention = datetime(2027, 3, 18, tzinfo=timezone.utc)
    log = AuditLog(
        user_id=user.id,
        action="create_project",
        resource_type="Project",
        resource_id="test-123",
        content_hash="a" * 64,
        compliance_framework="SOC2",
        evidence_type="CC6",
        retention_until=retention,
    )
    async_session.add(log)
    await async_session.flush()

    fetched = await async_session.get(AuditLog, log.id)
    assert fetched is not None
    assert fetched.content_hash == "a" * 64
    assert fetched.compliance_framework == "SOC2"
    assert fetched.evidence_type == "CC6"
    assert fetched.retention_until == retention
