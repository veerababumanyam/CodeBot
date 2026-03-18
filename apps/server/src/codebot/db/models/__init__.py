"""ORM model barrel — imports Base and every model so Alembic autogenerate discovers all tables."""

# Base and shared mixins
from codebot.db.models.base import Base, TimestampMixin

# Core pipeline models (order matters: User before Project due to FK)
from codebot.db.models.user import AuditLog, ApiKey, User, UserRole

# Project hierarchy
from codebot.db.models.project import (
    PhaseStatus,
    PhaseType,
    Pipeline,
    PipelinePhase,
    PipelineStatus,
    Project,
    ProjectStatus,
    ProjectType,
)

# Work models
from codebot.db.models.task import Task, TaskStatus
from codebot.db.models.agent import Agent, AgentExecution, AgentStatus, AgentType, ExecutionStatus

# Artifact and results
from codebot.db.models.artifact import ArtifactOperation, CodeArtifact
from codebot.db.models.test_result import TestResult, TestStatus

# Quality models
from codebot.db.models.security import FindingStatus, FindingType, SecurityFinding, Severity
from codebot.db.models.review import CommentStatus, CommentType, ReviewComment

# System models
from codebot.db.models.event import Event, EventType
from codebot.db.models.checkpoint import Checkpoint
from codebot.db.models.experiment import ExperimentLog, ExperimentStatus

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # User
    "User",
    "UserRole",
    "ApiKey",
    "AuditLog",
    # Project hierarchy
    "Project",
    "ProjectStatus",
    "ProjectType",
    "Pipeline",
    "PipelineStatus",
    "PipelinePhase",
    "PhaseType",
    "PhaseStatus",
    # Work
    "Task",
    "TaskStatus",
    "Agent",
    "AgentType",
    "AgentStatus",
    "AgentExecution",
    "ExecutionStatus",
    # Artifacts
    "CodeArtifact",
    "ArtifactOperation",
    # Results
    "TestResult",
    "TestStatus",
    # Quality
    "SecurityFinding",
    "FindingType",
    "FindingStatus",
    "Severity",
    "ReviewComment",
    "CommentType",
    "CommentStatus",
    # System
    "Event",
    "EventType",
    "Checkpoint",
    "ExperimentLog",
    "ExperimentStatus",
]
