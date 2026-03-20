"""DebuggerAgent -- performs root cause analysis and iterative fix generation.

Implements the PRA cognitive cycle:
- perceive(): Reads test failures and source files from shared state
- reason(): Uses FailureAnalyzer to identify root cause via LLM
- act(): Runs experiment loop: analyze -> generate fix -> apply -> re-test
- review(): Returns AgentOutput with tests_passing, experiment_log, final_pass_rate

Uses ExperimentLoopController with circuit breakers and KEEP/DISCARD semantics.
Each fix is measured against the stable baseline. Improvements are KEEP
(source updated), regressions are DISCARD (source reverted).
"""

from __future__ import annotations

import logging
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.debug.analyzer import FailureAnalyzer
from codebot.debug.fixer import FixGenerator
from codebot.debug.loop_controller import ExperimentLoopController
from codebot.testing.parser import TestResultParser
from codebot.testing.runner import TestRunner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are a senior software debugger specializing in Python applications.
You perform methodical root cause analysis and generate targeted, minimal fixes.
</role>

<responsibilities>
- Parse stack traces to identify the exact failure point
- Read affected source code to understand the context
- Identify the root cause (not just the symptom)
- Generate minimal, targeted fixes that resolve the issue
- Preserve all existing functionality and code style
- Consider edge cases introduced by the fix
</responsibilities>

<constraints>
- Change only what is necessary to fix the identified issue
- Do not refactor or reorganize code beyond the fix
- Ensure fixes don't introduce new issues
- Preserve type annotations and docstrings
- Follow the existing code style (PEP 8, Google docstrings)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class DebuggerAgent(BaseAgent):
    """Performs root cause analysis and iterative fix generation.

    Uses the PRA cognitive cycle with ExperimentLoopController:
    1. Perceive test failures from shared state
    2. Reason about root cause via FailureAnalyzer
    3. Act by running experiment loop (fix -> test -> keep/discard)
    4. Review final results and set tests_passing status
    """

    agent_type: AgentType = field(default=AgentType.DEBUGGER, init=False)

    async def _initialize(self, agent_input: AgentInput) -> None:
        """Prepare for debug execution.

        Args:
            agent_input: The task input for initialization context.
        """
        # No additional initialization needed

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Read test failures and source files from shared state.

        Args:
            agent_input: The task input with shared state.

        Returns:
            Dict with test_failures, source_files, baseline_pass_rate, workspace_path.
        """
        test_failures = agent_input.shared_state.get("test_failures", [])
        source_files = agent_input.shared_state.get(
            "backend_dev.generated_files", {}
        )
        test_results = agent_input.shared_state.get("test_results", {})

        # Compute baseline pass rate from test results
        total = test_results.get("total", 1)
        passed = test_results.get("passed", 0)
        baseline_pass_rate = passed / total if total > 0 else 0.0

        workspace_path = agent_input.shared_state.get(
            "backend_dev.workspace", tempfile.gettempdir()
        )

        return {
            "test_failures": test_failures,
            "source_files": source_files,
            "baseline_pass_rate": baseline_pass_rate,
            "workspace_path": workspace_path,
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Perform root cause analysis via FailureAnalyzer.

        Args:
            context: Assembled context from perceive().

        Returns:
            Dict with analysis, test_failures, source_files, baseline_pass_rate,
            and workspace_path for the act() phase.
        """
        analyzer = FailureAnalyzer()
        analysis = await analyzer.analyze(
            failure_details=context.get("test_failures", []),
            source_files=context.get("source_files", {}),
        )

        logger.info(
            "Root cause identified: %s (confidence: %.2f)",
            analysis.root_cause,
            analysis.confidence,
        )

        return {
            "analysis": analysis,
            "test_failures": context.get("test_failures", []),
            "source_files": context.get("source_files", {}),
            "baseline_pass_rate": context.get("baseline_pass_rate", 0.0),
            "workspace_path": context.get("workspace_path", tempfile.gettempdir()),
        }

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Run experiment loop: generate fix -> apply -> re-test.

        Uses ExperimentLoopController with circuit breakers. Each fix
        is evaluated against the baseline. KEEP if improved, DISCARD
        if not (source reverted to pre-fix state).

        Args:
            plan: Dict from reason() with analysis and context.

        Returns:
            PRAResult with experiment log and final pass rate.
        """
        analysis = plan["analysis"]
        source_files = dict(plan.get("source_files", {}))
        baseline_pass_rate = plan.get("baseline_pass_rate", 0.0)
        workspace = plan.get("workspace_path", tempfile.gettempdir())

        fixer = FixGenerator()
        runner = TestRunner()
        controller = ExperimentLoopController()

        current_pass_rate = baseline_pass_rate
        experiment_id = 0

        while controller.should_continue(baseline_pass_rate, current_pass_rate):
            experiment_id += 1
            start_time = time.monotonic()

            # Save pre-fix state for revert on DISCARD
            pre_fix_files = dict(source_files)

            # Generate fix
            fixes = await fixer.generate(analysis, source_files)
            total_diff_lines = sum(f.diff_lines for f in fixes)

            # Apply fix
            await fixer.apply(fixes, workspace)

            # Re-run tests
            test_report, coverage_data = await runner.run(workspace)
            parsed = TestResultParser.parse(test_report, coverage_data)

            # Compute new pass rate
            new_pass_rate = (
                parsed.passed / parsed.total if parsed.total > 0 else 0.0
            )

            duration = time.monotonic() - start_time

            # Record experiment
            result = controller.record_experiment(
                experiment_id=experiment_id,
                hypothesis=fixes[0].hypothesis if fixes else "unknown",
                metric_before=current_pass_rate,
                metric_after=new_pass_rate,
                duration_seconds=duration,
                diff_lines=total_diff_lines,
            )

            if result.status == "KEEP":
                # Update source files with fixed content
                for fix in fixes:
                    source_files[fix.file_path] = fix.fixed_content
                current_pass_rate = new_pass_rate
                logger.info(
                    "Experiment %d KEEP: pass rate %.2f -> %.2f",
                    experiment_id,
                    result.metric_before,
                    result.metric_after,
                )
            else:
                # Revert to pre-fix state
                source_files = pre_fix_files
                logger.info(
                    "Experiment %d DISCARD: pass rate %.2f -> %.2f",
                    experiment_id,
                    result.metric_before,
                    result.metric_after,
                )

        experiment_log = [
            {
                "experiment_id": e.experiment_id,
                "hypothesis": e.hypothesis,
                "status": e.status,
                "delta": e.delta,
                "metric_before": e.metric_before,
                "metric_after": e.metric_after,
                "duration_seconds": e.duration_seconds,
            }
            for e in controller.experiments
        ]

        tests_passing = current_pass_rate >= 1.0

        return PRAResult(
            is_complete=True,
            data={
                "tests_passing": tests_passing,
                "final_pass_rate": current_pass_rate,
                "experiment_log": experiment_log,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Return AgentOutput with tests_passing, experiment_log, final_pass_rate.

        Args:
            result: PRAResult from act() with experiment data.

        Returns:
            AgentOutput with state_updates for downstream agents.
        """
        data = result.data
        tests_passing = bool(data.get("tests_passing", False))

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={
                "tests_passing": tests_passing,
                "final_pass_rate": data.get("final_pass_rate", 0.0),
                "experiment_log": data.get("experiment_log", []),
            },
            review_passed=tests_passing,
        )
