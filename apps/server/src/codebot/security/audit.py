"""Immutable audit logger with SHA-256 tamper-detection hashing.

Wraps the :class:`AuditLog` ORM model with content hashing, compliance
framework tagging, and retention policy enforcement.  Provides a
:meth:`verify` method to detect tampered entries by recomputing hashes.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from codebot.db.models.user import AuditLog
from codebot.security.compliance.models import ComplianceFramework

# Retention periods per compliance framework (in days)
_RETENTION_DAYS: dict[ComplianceFramework, int] = {
    ComplianceFramework.SOC2: 365,
    ComplianceFramework.HIPAA: 2190,  # 6 years
    ComplianceFramework.GDPR: 1095,  # 3 years (depends on purpose)
    ComplianceFramework.PCI_DSS: 365,
}


class ImmutableAuditLogger:
    """Audit logger that computes SHA-256 content hashes for tamper detection.

    Args:
        session: SQLAlchemy async session for persisting log entries.
        framework: Optional compliance framework for tagging entries.
    """

    def __init__(
        self,
        session: Any,
        framework: ComplianceFramework | None = None,
    ) -> None:
        self.session = session
        self.framework = framework

    def log(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        evidence_type: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry with content hash and compliance metadata.

        Args:
            action: Verb describing the action (e.g. ``create_project``).
            resource_type: Resource class (e.g. ``Project``).
            resource_id: String ID of the affected resource.
            user_id: Optional FK to the acting user.
            details: Arbitrary JSON payload.
            ip_address: Client IP at time of action.
            user_agent: HTTP User-Agent header.
            evidence_type: TSC category (e.g. ``CC6``, ``CC7``).

        Returns:
            The created :class:`AuditLog` entry with computed content_hash.
        """
        now = datetime.now(UTC)

        # Compute content hash from canonical fields
        content_hash = self._compute_hash(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )

        # Compute retention_until from framework
        retention_until: datetime | None = None
        if self.framework is not None:
            days = _RETENTION_DAYS.get(self.framework, 365)
            retention_until = now + timedelta(days=days)

        entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            content_hash=content_hash,
            compliance_framework=self.framework.value if self.framework else None,
            evidence_type=evidence_type,
            retention_until=retention_until,
            created_at=now,
        )

        self.session.add(entry)
        return entry

    def verify(self, entry: AuditLog) -> bool:
        """Verify an audit log entry has not been tampered with.

        Recomputes the SHA-256 hash from the entry's fields and compares
        it to the stored ``content_hash``.

        Args:
            entry: The audit log entry to verify.

        Returns:
            ``True`` if the hash matches, ``False`` if tampered.
        """
        if entry.content_hash is None:
            return False

        expected = self._compute_hash(
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            details=entry.details,
        )
        return entry.content_hash == expected

    @staticmethod
    def _compute_hash(
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Compute SHA-256 hash from canonical audit entry fields.

        Uses JSON serialization with sorted keys for deterministic output.

        Args:
            action: The action verb.
            resource_type: The resource class.
            resource_id: The resource identifier.
            details: Optional JSON details payload.

        Returns:
            64-character hex digest of the SHA-256 hash.
        """
        payload = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
        }
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
