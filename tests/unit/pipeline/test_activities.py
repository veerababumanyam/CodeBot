"""Tests for Temporal activities: load_pipeline_config, execute_phase_activity, emit_pipeline_event.

These tests mock the Temporal activity context and verify that activities
have the correct decorator, use heartbeats, and produce expected outputs.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.pipeline.activities import (
    emit_pipeline_event,
    execute_phase_activity,
    load_pipeline_config,
)
from codebot.pipeline.checkpoint import PhaseInput


class TestLoadPipelineConfig:
    """Tests for load_pipeline_config activity."""

    def test_is_activity(self) -> None:
        """load_pipeline_config is decorated with @activity.defn."""
        assert hasattr(load_pipeline_config, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_returns_dict(self) -> None:
        """load_pipeline_config returns a dict (serialized PipelineConfig)."""
        with patch("codebot.pipeline.activities.load_preset") as mock_load:
            mock_config = MagicMock()
            mock_config.model_dump.return_value = {
                "name": "full",
                "version": "1.0",
                "phases": [],
            }
            mock_load.return_value = mock_config

            with patch("codebot.pipeline.activities.activity"):
                result = await load_pipeline_config("full")

            assert isinstance(result, dict)
            assert result["name"] == "full"


class TestExecutePhaseActivity:
    """Tests for execute_phase_activity."""

    def test_is_activity(self) -> None:
        """execute_phase_activity is decorated with @activity.defn."""
        assert hasattr(execute_phase_activity, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_returns_phase_result(self) -> None:
        """execute_phase_activity returns a PhaseResult."""
        phase_input = PhaseInput(
            project_id="proj-1",
            phase_name="design",
            phase_idx=3,
            agents=["architect", "designer"],
            parallel=False,
            config={},
        )

        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            result = await execute_phase_activity(phase_input)

        assert result.phase_name == "design"
        assert result.phase_idx == 3
        assert result.status == "completed"
        assert len(result.agent_results) == 2

    @pytest.mark.asyncio
    async def test_heartbeats_per_agent(self) -> None:
        """execute_phase_activity calls heartbeat for each agent."""
        phase_input = PhaseInput(
            project_id="proj-1",
            phase_name="implement",
            phase_idx=5,
            agents=["backend_dev", "frontend_dev", "infra_engineer"],
            parallel=False,
            config={},
        )

        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            await execute_phase_activity(phase_input)

        # 1 starting heartbeat + 3 agent heartbeats = 4 calls
        assert mock_activity.heartbeat.call_count == 4

    @pytest.mark.asyncio
    async def test_agent_results_structure(self) -> None:
        """Each agent result has agent, status, and output keys."""
        phase_input = PhaseInput(
            project_id="proj-1",
            phase_name="design",
            phase_idx=3,
            agents=["architect"],
            parallel=False,
            config={},
        )

        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            result = await execute_phase_activity(phase_input)

        agent_result = result.agent_results[0]
        assert agent_result["agent"] == "architect"
        assert agent_result["status"] == "completed"
        assert "output" in agent_result


class TestEmitPipelineEvent:
    """Tests for emit_pipeline_event activity."""

    def test_is_activity(self) -> None:
        """emit_pipeline_event is decorated with @activity.defn."""
        assert hasattr(emit_pipeline_event, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_emits_heartbeat(self) -> None:
        """emit_pipeline_event calls heartbeat with event type."""
        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            await emit_pipeline_event({"type": "pipeline.phase_started"})

        mock_activity.heartbeat.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_event(self) -> None:
        """emit_pipeline_event logs the event type and timestamp."""
        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            await emit_pipeline_event({"type": "pipeline.phase_completed"})

        mock_activity.logger.info.assert_called_once()
        call_args = mock_activity.logger.info.call_args
        assert "pipeline.phase_completed" in str(call_args)

    @pytest.mark.asyncio
    async def test_returns_none(self) -> None:
        """emit_pipeline_event returns None."""
        with patch("codebot.pipeline.activities.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            mock_activity.logger = MagicMock()

            result = await emit_pipeline_event({"type": "test"})

        assert result is None
