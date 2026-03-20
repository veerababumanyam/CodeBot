"""Tests for NATS-to-Socket.IO event bridge."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from codebot.websocket.bridge import _bridge_loop


def _make_nats_msg(subject: str, data: dict) -> MagicMock:
    """Create a mock NATS message with the given subject and JSON data."""
    msg = MagicMock()
    msg.subject = subject
    msg.data = json.dumps(data).encode()
    msg.ack = AsyncMock()
    return msg


@pytest.mark.integration
class TestBridge:
    """Tests for the NATS-to-Socket.IO bridge event routing."""

    async def test_bridge_extracts_event_name(self) -> None:
        """Bridge strips codebot.events. prefix and emits to project room."""
        sio_mock = AsyncMock()
        msg = _make_nats_msg(
            "codebot.events.pipeline.phase_changed",
            {"project_id": "abc", "from_phase": "plan"},
        )

        sub_mock = AsyncMock()
        sub_mock.next_msg = AsyncMock(
            side_effect=[msg, asyncio.TimeoutError, asyncio.CancelledError]
        )

        try:
            await _bridge_loop(sio_mock, sub_mock)
        except asyncio.CancelledError:
            pass

        sio_mock.emit.assert_called_once_with(
            "pipeline.phase_changed",
            {"project_id": "abc", "from_phase": "plan"},
            room="project:abc",
        )
        msg.ack.assert_called_once()

    async def test_bridge_broadcasts_without_project_id(self) -> None:
        """Bridge emits to all clients when no project_id in payload."""
        sio_mock = AsyncMock()
        msg = _make_nats_msg(
            "codebot.events.system.health",
            {"status": "healthy"},
        )

        sub_mock = AsyncMock()
        sub_mock.next_msg = AsyncMock(
            side_effect=[msg, asyncio.TimeoutError, asyncio.CancelledError]
        )

        try:
            await _bridge_loop(sio_mock, sub_mock)
        except asyncio.CancelledError:
            pass

        sio_mock.emit.assert_called_once_with(
            "system.health",
            {"status": "healthy"},
        )
        msg.ack.assert_called_once()

    async def test_bridge_handles_timeout_gracefully(self) -> None:
        """Bridge continues running on subscription timeout."""
        sio_mock = AsyncMock()

        sub_mock = AsyncMock()
        sub_mock.next_msg = AsyncMock(
            side_effect=[
                asyncio.TimeoutError,
                asyncio.TimeoutError,
                asyncio.CancelledError,
            ]
        )

        try:
            await _bridge_loop(sio_mock, sub_mock)
        except asyncio.CancelledError:
            pass

        # No emit calls should have been made on timeouts
        sio_mock.emit.assert_not_called()
