"""Compliance evidence collector -- structured JSON export for auditors.

Collects evidence entries grouped by Trust Service Criteria categories
and exports them as structured JSON packages suitable for SOC 2 Type II
auditor review.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from codebot.security.compliance.models import TrustServiceCategory


class ComplianceEvidenceCollector:
    """Collects and exports compliance evidence as structured JSON.

    Evidence entries are grouped by TSC category and include timestamps
    and type metadata for auditor traceability.
    """

    def __init__(self) -> None:
        self._evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_evidence(
        self,
        *,
        category: TrustServiceCategory,
        evidence_type: str,
        data: dict[str, Any],
        collected_at: datetime | None = None,
    ) -> None:
        """Add an evidence entry to the collector.

        Args:
            category: TSC category this evidence relates to.
            evidence_type: Type of evidence (e.g. ``scan_result``,
                ``audit_log``, ``config``, ``health_check``).
            data: Arbitrary evidence payload.
            collected_at: Timestamp when evidence was collected.
                Defaults to current UTC time.
        """
        timestamp = collected_at or datetime.now(UTC)
        self._evidence[category.value].append(
            {
                "evidence_type": evidence_type,
                "data": data,
                "collected_at": timestamp.isoformat(),
            }
        )

    def export(self) -> dict[str, list[dict[str, Any]]]:
        """Export all collected evidence grouped by TSC category.

        Returns:
            A dict mapping TSC category strings to lists of evidence
            entries.  Each entry contains ``evidence_type``, ``data``,
            and ``collected_at`` fields.
        """
        return dict(self._evidence)

    def export_json(self, *, indent: int = 2) -> str:
        """Export evidence as a JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            Pretty-printed JSON string of the evidence package.
        """
        return json.dumps(self.export(), indent=indent, default=str)

    def clear(self) -> None:
        """Remove all collected evidence."""
        self._evidence.clear()
