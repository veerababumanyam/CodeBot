"""Clarification loop for detecting ambiguous or incomplete requirements.

Analyzes ``ExtractedRequirements`` for low-confidence scores, explicit
ambiguities, and missing acceptance criteria.  The results drive the
Orchestrator's decision to request clarification or proceed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from codebot.input.models import ExtractedRequirements


@dataclass(slots=True, kw_only=True)
class ClarificationItem:
    """A single item needing human clarification.

    Attributes:
        source: Origin of the clarification need -- "low_confidence",
            "ambiguity", or "missing_criteria".
        requirement_id: Related FR identifier (e.g. FR-01), or None
            for general ambiguities.
        description: Human-readable description of what needs clarification.
        confidence: The confidence score that triggered this item, or None.
    """

    source: str
    requirement_id: str | None
    description: str
    confidence: float | None


@dataclass(slots=True, kw_only=True)
class ClarificationLoop:
    """Detect ambiguities and low-confidence items in extracted requirements.

    Attributes:
        confidence_threshold: Minimum confidence score (default 0.7).
            Requirements below this threshold are flagged.
    """

    confidence_threshold: float = 0.7
    _items: list[ClarificationItem] = field(default_factory=list)

    def check(self, requirements: ExtractedRequirements) -> list[ClarificationItem]:
        """Analyze requirements for issues needing clarification.

        Checks three categories:
        1. Functional requirements with confidence below threshold.
        2. Entries in the ``ambiguities`` list.
        3. Functional requirements with empty ``acceptance_criteria``.

        Args:
            requirements: The extracted requirements to analyze.

        Returns:
            List of ClarificationItem objects describing each issue.
        """
        self._items = []

        # 1. Low confidence requirements
        for fr in requirements.functional_requirements:
            if fr.confidence < self.confidence_threshold:
                self._items.append(
                    ClarificationItem(
                        source="low_confidence",
                        requirement_id=fr.id,
                        description=(
                            f"Requirement '{fr.title}' has low confidence "
                            f"({fr.confidence:.2f} < {self.confidence_threshold})"
                        ),
                        confidence=fr.confidence,
                    )
                )

        # 2. Explicit ambiguities from extraction
        for ambiguity in requirements.ambiguities:
            self._items.append(
                ClarificationItem(
                    source="ambiguity",
                    requirement_id=None,
                    description=ambiguity,
                    confidence=None,
                )
            )

        # 3. Missing acceptance criteria
        for fr in requirements.functional_requirements:
            if not fr.acceptance_criteria:
                self._items.append(
                    ClarificationItem(
                        source="missing_criteria",
                        requirement_id=fr.id,
                        description=(
                            f"Requirement '{fr.title}' has no acceptance criteria"
                        ),
                        confidence=None,
                    )
                )

        return self._items

    @property
    def needs_clarification(self) -> bool:
        """Whether any clarification items exist after the last check."""
        return len(self._items) > 0
