"""Unit tests for ExperimentLoopController.

Tests cover circuit breakers and KEEP/DISCARD semantics:
- should_continue() returns False when all tests pass
- should_continue() returns False when max experiments reached
- should_continue() returns False when time budget exhausted
- should_continue() returns False after max_no_improvement consecutive DISCARDs
- should_continue() returns True when budgets remain and tests still failing
- record_experiment() marks KEEP when improvement exceeds threshold
- record_experiment() marks DISCARD when no improvement
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# ExperimentResult model
# ---------------------------------------------------------------------------


class TestExperimentResult:
    """ExperimentResult contains required fields."""

    def test_experiment_result_has_required_fields(self) -> None:
        from codebot.debug.loop_controller import ExperimentResult

        result = ExperimentResult(
            experiment_id=1,
            hypothesis="Fix null check in get_item",
            metric_before=0.6,
            metric_after=0.8,
            delta=0.2,
            status="KEEP",
        )
        assert result.experiment_id == 1
        assert result.hypothesis == "Fix null check in get_item"
        assert result.metric_before == 0.6
        assert result.metric_after == 0.8
        assert result.delta == 0.2
        assert result.status == "KEEP"
        assert result.commit_hash == ""
        assert result.diff_lines == 0
        assert result.duration_seconds == 0.0


# ---------------------------------------------------------------------------
# ExperimentLoopController.should_continue()
# ---------------------------------------------------------------------------


class TestShouldContinue:
    """ExperimentLoopController.should_continue() circuit breakers."""

    def test_returns_false_when_all_tests_pass(self) -> None:
        """All tests pass (pass_rate >= 1.0) -> stop."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController()
        assert controller.should_continue(0.5, 1.0) is False

    def test_returns_false_when_max_experiments_reached(self) -> None:
        """Max experiments reached -> stop."""
        from codebot.debug.loop_controller import (
            ExperimentLoopController,
            ExperimentResult,
        )

        controller = ExperimentLoopController(max_experiments=2)
        controller.experiments = [
            ExperimentResult(
                experiment_id=i,
                hypothesis=f"fix {i}",
                metric_before=0.5,
                metric_after=0.6,
                delta=0.1,
                status="KEEP",
                duration_seconds=10.0,
            )
            for i in range(2)
        ]
        assert controller.should_continue(0.5, 0.6) is False

    def test_returns_false_when_time_budget_exhausted(self) -> None:
        """Time budget exhausted -> stop."""
        from codebot.debug.loop_controller import (
            ExperimentLoopController,
            ExperimentResult,
        )

        controller = ExperimentLoopController(time_budget_seconds=30.0)
        controller.experiments = [
            ExperimentResult(
                experiment_id=1,
                hypothesis="fix 1",
                metric_before=0.5,
                metric_after=0.6,
                delta=0.1,
                status="KEEP",
                duration_seconds=35.0,
            )
        ]
        assert controller.should_continue(0.5, 0.6) is False

    def test_returns_false_after_max_no_improvement(self) -> None:
        """Consecutive DISCARDs exceeding max_no_improvement -> stop."""
        from codebot.debug.loop_controller import (
            ExperimentLoopController,
            ExperimentResult,
        )

        controller = ExperimentLoopController(max_no_improvement=3)
        controller.experiments = [
            ExperimentResult(
                experiment_id=i,
                hypothesis=f"fix {i}",
                metric_before=0.5,
                metric_after=0.5,
                delta=0.0,
                status="DISCARD",
                duration_seconds=5.0,
            )
            for i in range(3)
        ]
        assert controller.should_continue(0.5, 0.5) is False

    def test_returns_true_when_tests_still_failing_and_budgets_remain(self) -> None:
        """Tests still failing, no circuit breaker triggered -> continue."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController(
            max_experiments=5,
            time_budget_seconds=600.0,
            max_no_improvement=3,
        )
        assert controller.should_continue(0.5, 0.7) is True

    def test_experiment_loop(self) -> None:
        """Integration: loop with mixed KEEP/DISCARD experiments."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController(
            max_experiments=5,
            time_budget_seconds=600.0,
            max_no_improvement=3,
        )

        # First experiment: improvement (KEEP)
        r1 = controller.record_experiment(
            experiment_id=1,
            hypothesis="Fix null check",
            metric_before=0.5,
            metric_after=0.7,
            duration_seconds=10.0,
        )
        assert r1.status == "KEEP"
        assert controller.should_continue(0.5, 0.7) is True

        # Second experiment: no improvement (DISCARD)
        r2 = controller.record_experiment(
            experiment_id=2,
            hypothesis="Try different approach",
            metric_before=0.7,
            metric_after=0.7,
            duration_seconds=10.0,
        )
        assert r2.status == "DISCARD"
        assert controller.should_continue(0.5, 0.7) is True

        # Third: all pass -> stop
        assert controller.should_continue(0.5, 1.0) is False


# ---------------------------------------------------------------------------
# ExperimentLoopController.record_experiment()
# ---------------------------------------------------------------------------


class TestRecordExperiment:
    """ExperimentLoopController.record_experiment() KEEP/DISCARD logic."""

    def test_marks_keep_when_improvement_exceeds_threshold(self) -> None:
        """Metric improved beyond threshold -> KEEP."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController(improvement_threshold=0.01)
        result = controller.record_experiment(
            experiment_id=1,
            hypothesis="Fix auth check",
            metric_before=0.6,
            metric_after=0.8,
            duration_seconds=15.0,
        )
        assert result.status == "KEEP"
        assert result.delta == pytest.approx(0.2)

    def test_marks_discard_when_no_improvement(self) -> None:
        """Metric not improved -> DISCARD."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController(improvement_threshold=0.01)
        result = controller.record_experiment(
            experiment_id=1,
            hypothesis="Bad fix attempt",
            metric_before=0.6,
            metric_after=0.6,
            duration_seconds=10.0,
        )
        assert result.status == "DISCARD"
        assert result.delta == pytest.approx(0.0)

    def test_marks_discard_when_regression(self) -> None:
        """Metric regressed -> DISCARD."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController(improvement_threshold=0.01)
        result = controller.record_experiment(
            experiment_id=1,
            hypothesis="Regression fix",
            metric_before=0.8,
            metric_after=0.5,
            duration_seconds=5.0,
        )
        assert result.status == "DISCARD"
        assert result.delta == pytest.approx(-0.3)

    def test_records_experiment_in_list(self) -> None:
        """record_experiment appends to experiments list."""
        from codebot.debug.loop_controller import ExperimentLoopController

        controller = ExperimentLoopController()
        controller.record_experiment(
            experiment_id=1,
            hypothesis="fix 1",
            metric_before=0.5,
            metric_after=0.7,
            duration_seconds=10.0,
        )
        assert len(controller.experiments) == 1
        assert controller.experiments[0].experiment_id == 1
