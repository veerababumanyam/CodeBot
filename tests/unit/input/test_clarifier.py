"""Unit tests for ClarificationLoop and ClarificationItem."""

from __future__ import annotations

from codebot.input.clarifier import ClarificationItem, ClarificationLoop
from codebot.input.models import (
    AcceptanceCriterion,
    ExtractedRequirements,
    FunctionalRequirement,
)


class TestClarificationLoop:
    """ClarificationLoop detects ambiguities and low-confidence requirements."""

    def _make_requirements(
        self,
        *,
        confidences: list[float] | None = None,
        ambiguities: list[str] | None = None,
        empty_criteria: bool = False,
    ) -> ExtractedRequirements:
        """Helper to build ExtractedRequirements with configurable params."""
        if confidences is None:
            confidences = [0.95]

        frs = []
        for i, conf in enumerate(confidences):
            criteria = (
                []
                if empty_criteria
                else [
                    AcceptanceCriterion(
                        description=f"Criterion for FR-{i + 1:02d}",
                        test_strategy="unit_test",
                    )
                ]
            )
            frs.append(
                FunctionalRequirement(
                    id=f"FR-{i + 1:02d}",
                    title=f"Requirement {i + 1}",
                    description=f"Description for requirement {i + 1}",
                    priority="Must",
                    acceptance_criteria=criteria,
                    confidence=conf,
                )
            )
        return ExtractedRequirements(
            project_name="Test Project",
            project_description="A test project",
            functional_requirements=frs,
            non_functional_requirements=[],
            constraints=[],
            ambiguities=ambiguities or [],
        )

    def test_no_clarification_needed(self) -> None:
        """Returns empty list when all requirements have confidence >= 0.7 and no ambiguities."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(confidences=[0.95, 0.8])
        items = loop.check(reqs)
        assert items == []
        assert not loop.needs_clarification

    def test_low_confidence_triggers_clarification(self) -> None:
        """Returns clarification items when any requirement has confidence < 0.7."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(confidences=[0.95, 0.5])
        items = loop.check(reqs)
        assert len(items) >= 1
        low_conf_items = [i for i in items if i.source == "low_confidence"]
        assert len(low_conf_items) >= 1
        assert low_conf_items[0].requirement_id == "FR-02"
        assert low_conf_items[0].confidence == 0.5

    def test_ambiguity_detection(self) -> None:
        """Returns clarification items when ambiguities list is non-empty."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(ambiguities=["What database to use?"])
        items = loop.check(reqs)
        assert len(items) >= 1
        ambiguity_items = [i for i in items if i.source == "ambiguity"]
        assert len(ambiguity_items) >= 1
        assert "What database to use?" in ambiguity_items[0].description

    def test_missing_criteria_triggers_clarification(self) -> None:
        """Returns clarification items when FRs have empty acceptance_criteria."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(confidences=[0.95], empty_criteria=True)
        items = loop.check(reqs)
        missing_items = [i for i in items if i.source == "missing_criteria"]
        assert len(missing_items) >= 1
        assert missing_items[0].requirement_id == "FR-01"

    def test_needs_clarification_property_true(self) -> None:
        """needs_clarification returns True when check() returns non-empty list."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(confidences=[0.3])
        loop.check(reqs)
        assert loop.needs_clarification is True

    def test_needs_clarification_property_false(self) -> None:
        """needs_clarification returns False when check() returns empty list."""
        loop = ClarificationLoop()
        reqs = self._make_requirements(confidences=[0.95])
        loop.check(reqs)
        assert loop.needs_clarification is False

    def test_custom_confidence_threshold(self) -> None:
        """Respects custom confidence_threshold."""
        loop = ClarificationLoop(confidence_threshold=0.9)
        reqs = self._make_requirements(confidences=[0.85])
        items = loop.check(reqs)
        low_conf = [i for i in items if i.source == "low_confidence"]
        assert len(low_conf) >= 1


class TestClarificationItem:
    """ClarificationItem fields are accessible."""

    def test_fields(self) -> None:
        item = ClarificationItem(
            source="low_confidence",
            requirement_id="FR-01",
            description="Low confidence on FR-01",
            confidence=0.4,
        )
        assert item.source == "low_confidence"
        assert item.requirement_id == "FR-01"
        assert item.confidence == 0.4
