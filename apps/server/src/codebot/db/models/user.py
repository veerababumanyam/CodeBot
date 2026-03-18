"""User, ApiKey, and AuditLog ORM models."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class UserRole(enum.Enum):
    """Roles available to CodeBot users."""

    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class User(Base):
    """A CodeBot platform user.

    Attributes:
        id: Primary key UUID.
        email: Unique email address used for login.
        password_hash: Bcrypt (or Argon2) hash of the user's password.
        name: Display name.
        role: Access role (ADMIN / USER / VIEWER).
        organization: Optional org name.
        mfa_secret: Encrypted TOTP secret when MFA is enabled.
        mfa_enabled: Whether MFA is active for this account.
        preferences: Arbitrary JSON preferences blob.
        created_at: Account creation timestamp.
        updated_at: Last profile update timestamp.
        last_login_at: Most recent successful login.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="userrole", create_constraint=True),
        nullable=False,
        default=UserRole.USER,
    )
    organization: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    mfa_secret: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    preferences: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


class ApiKey(Base):
    """A hashed API key belonging to a user.

    Attributes:
        id: Primary key UUID.
        user_id: Foreign key to the owning User.
        name: Human-readable label for the key.
        key_hash: SHA-256 hash of the raw API key.
        key_prefix: First 8 characters of the raw key (for display).
        last_used_at: When the key was last used to authenticate.
        expires_at: Optional expiry timestamp.
        created_at: Creation timestamp.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    key_prefix: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")


class AuditLog(Base):
    """Immutable audit log entry recording an action taken by a user.

    Database-level immutability is enforced via PostgreSQL rules that prevent
    UPDATE and DELETE operations on the ``audit_logs`` table.

    Attributes:
        id: Primary key UUID.
        user_id: Optional FK to the acting User (null = system action).
        action: Verb describing what happened (e.g. ``create_project``).
        resource_type: Resource class (e.g. ``Project``, ``Pipeline``).
        resource_id: String representation of the affected resource ID.
        details: Arbitrary JSON payload with contextual details.
        ip_address: Client IP at time of action.
        user_agent: HTTP User-Agent header.
        content_hash: SHA-256 tamper-detection hash of the log entry payload.
        compliance_framework: Applicable framework (SOC2, HIPAA, GDPR, PCI_DSS).
        evidence_type: Trust Service Criteria category (e.g. CC6, CC7, CC8, CC9).
        retention_until: Retention expiry per compliance policy.
        created_at: When the action occurred.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    resource_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    details: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True, comment="SHA-256 tamper-detection hash"
    )
    compliance_framework: Mapped[str | None] = mapped_column(
        sa.String(32), nullable=True, comment="SOC2, HIPAA, GDPR, PCI_DSS"
    )
    evidence_type: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True, comment="TSC category e.g. CC6, CC7, CC8, CC9"
    )
    retention_until: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, comment="Retention expiry per compliance policy"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
