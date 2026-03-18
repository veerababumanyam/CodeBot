"""Tests for AgentMetrics collection."""

from __future__ import annotations

import time

from agent_sdk.agents.metrics import AgentMetrics


class TestAgentMetrics:
    def test_initial_metrics_are_zero(self) -> None:
        metrics = AgentMetrics()
        assert metrics.execution_time_ms == 0
        assert metrics.input_tokens == 0
        assert metrics.output_tokens == 0
        assert metrics.total_tokens == 0
        assert metrics.cost_usd == 0.0
        assert metrics.retry_count == 0
        assert metrics.llm_calls == 0

    def test_record_llm_call(self) -> None:
        metrics = AgentMetrics()
        metrics.record_llm_call(
            input_tokens=100, output_tokens=50, cost_usd=0.001, duration_ms=500
        )
        assert metrics.input_tokens == 100
        assert metrics.output_tokens == 50
        assert metrics.total_tokens == 150
        assert metrics.cost_usd == pytest.approx(0.001)
        assert metrics.llm_calls == 1

        # Second call accumulates
        metrics.record_llm_call(
            input_tokens=200, output_tokens=100, cost_usd=0.002, duration_ms=300
        )
        assert metrics.input_tokens == 300
        assert metrics.output_tokens == 150
        assert metrics.total_tokens == 450
        assert metrics.cost_usd == pytest.approx(0.003)
        assert metrics.llm_calls == 2

    def test_record_retry(self) -> None:
        metrics = AgentMetrics()
        assert metrics.retry_count == 0
        metrics.record_retry()
        assert metrics.retry_count == 1
        metrics.record_retry()
        assert metrics.retry_count == 2

    def test_elapsed_time_ms(self) -> None:
        metrics = AgentMetrics()
        metrics.start()
        # Small sleep to ensure measurable time
        time.sleep(0.01)
        metrics.stop()
        assert metrics.execution_time_ms > 0

    def test_to_dict(self) -> None:
        metrics = AgentMetrics()
        metrics.record_llm_call(
            input_tokens=100, output_tokens=50, cost_usd=0.001, duration_ms=500
        )
        metrics.record_retry()
        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["cost_usd"] == pytest.approx(0.001)
        assert result["retry_count"] == 1
        assert result["llm_calls"] == 1
        assert "execution_time_ms" in result
        # Private fields should not be in dict
        assert "_start_ns" not in result
        assert "_stop_ns" not in result


# Need pytest import for approx
import pytest
