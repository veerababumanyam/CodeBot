"""ExperimentLoopController -- manages the debug-fix experiment loop.

Implements circuit breakers and KEEP/DISCARD semantics for the
Debugger agent's iterative fix cycle. Each fix attempt is measured
against a stable baseline; improvements are KEEP, regressions are DISCARD.

Circuit breakers:
1. All tests pass (pass_rate >= 1.0)
2. Max experiments reached
3. Time budget exhausted
4. Consecutive no-improvement streak
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class ExperimentResult:
    """Result of a single fix experiment.

    Attributes:
        experiment_id: Sequential experiment number.
        hypothesis: What this fix attempt is trying to resolve.
        commit_hash: Git commit hash of the experiment (empty if not committed).
        metric_before: Test pass rate before the fix (baseline).
        metric_after: Test pass rate after the fix.
        delta: metric_after - metric_before.
        status: KEEP if improved, DISCARD if not, CRASH/TIMEOUT on errors.
        diff_lines: Number of lines changed in the fix.
        duration_seconds: Time taken for this experiment.
    """

    experiment_id: int
    hypothesis: str
    commit_hash: str = ""
    metric_before: float
    metric_after: float
    delta: float
    status: str  # "KEEP", "DISCARD", "CRASH", "TIMEOUT"
    diff_lines: int = 0
    duration_seconds: float = 0.0


@dataclass(slots=True, kw_only=True)
class ExperimentLoopController:
    """Manages the debug-fix experiment loop with circuit breakers.

    Tracks experiments and enforces termination conditions to prevent
    infinite fix loops. Each experiment is independently evaluated
    against the baseline -- not against the previous attempt.

    Attributes:
        max_experiments: Maximum number of fix attempts before stopping.
        time_budget_seconds: Total time budget for all experiments.
        max_no_improvement: Stop after this many consecutive DISCARDs.
        improvement_threshold: Minimum delta to count as improvement.
        experiments: List of completed experiment results.
    """

    max_experiments: int = 5
    time_budget_seconds: float = 600.0
    max_no_improvement: int = 3
    improvement_threshold: float = 0.01

    experiments: list[ExperimentResult] = field(default_factory=list)

    def should_continue(
        self,
        baseline_pass_rate: float,
        current_pass_rate: float,
    ) -> bool:
        """Check all circuit breakers. Return False if any triggers.

        Args:
            baseline_pass_rate: Original pass rate before any fixes.
            current_pass_rate: Current pass rate after latest experiment.

        Returns:
            True if the loop should continue, False if any circuit
            breaker has been triggered.
        """
        # 1. All tests pass
        if current_pass_rate >= 1.0:
            return False

        # 2. Max experiments reached
        if len(self.experiments) >= self.max_experiments:
            return False

        # 3. Time budget exhausted
        total_time = sum(e.duration_seconds for e in self.experiments)
        if total_time >= self.time_budget_seconds:
            return False

        # 4. Consecutive no-improvement streak
        if len(self.experiments) >= self.max_no_improvement:
            recent = self.experiments[-self.max_no_improvement :]
            if all(e.status == "DISCARD" for e in recent):
                return False

        return True

    def record_experiment(
        self,
        experiment_id: int,
        hypothesis: str,
        metric_before: float,
        metric_after: float,
        duration_seconds: float,
        diff_lines: int = 0,
        commit_hash: str = "",
    ) -> ExperimentResult:
        """Record an experiment and determine KEEP/DISCARD.

        An experiment is KEEP when the metric improvement exceeds the
        threshold. Otherwise it is DISCARD. The delta is always computed
        as metric_after - metric_before.

        Args:
            experiment_id: Sequential experiment number.
            hypothesis: What this fix attempt was trying to resolve.
            metric_before: Test pass rate before the fix.
            metric_after: Test pass rate after the fix.
            duration_seconds: Time taken for this experiment.
            diff_lines: Number of lines changed.
            commit_hash: Git commit hash if committed.

        Returns:
            ExperimentResult with computed delta and status.
        """
        delta = metric_after - metric_before
        status = "KEEP" if delta > self.improvement_threshold else "DISCARD"

        result = ExperimentResult(
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            commit_hash=commit_hash,
            metric_before=metric_before,
            metric_after=metric_after,
            delta=delta,
            status=status,
            diff_lines=diff_lines,
            duration_seconds=duration_seconds,
        )
        self.experiments.append(result)
        return result
