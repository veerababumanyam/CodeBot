"""NATS-to-Socket.IO event forwarding bridge.

Subscribes to all NATS JetStream events and forwards them to the
appropriate Socket.IO rooms based on ``project_id`` in the payload.
"""

from __future__ import annotations

import asyncio
import json
import logging

import socketio

from codebot.events.bus import EventBus

logger = logging.getLogger(__name__)

_SUBJECT_PREFIX = "codebot.events."


async def start_nats_bridge(
    sio: socketio.AsyncServer,
    bus: EventBus,
) -> asyncio.Task:  # type: ignore[type-arg]
    """Start the NATS-to-Socket.IO bridge as a background task.

    Subscribes to all events on the codebot.events.> subject and
    creates a task that forwards them to Socket.IO rooms.

    Args:
        sio: The Socket.IO async server.
        bus: A connected EventBus instance.

    Returns:
        The background asyncio.Task (caller can cancel on shutdown).
    """
    sub = await bus.subscribe(">")
    bridge_task: asyncio.Task = asyncio.create_task(_bridge_loop(sio, sub))  # type: ignore[type-arg]
    logger.info("NATS-to-Socket.IO bridge started")
    return bridge_task


async def _bridge_loop(
    sio: socketio.AsyncServer,
    sub: object,
) -> None:
    """Continuously forward NATS messages to Socket.IO rooms.

    Args:
        sio: The Socket.IO async server.
        sub: NATS JetStream push subscription.
    """
    while True:
        try:
            msg = await sub.next_msg(timeout=5.0)  # type: ignore[union-attr]
        except TimeoutError:
            continue
        except Exception:
            logger.debug("Bridge loop error waiting for message", exc_info=True)
            continue

        try:
            data = json.loads(msg.data.decode())
            project_id = data.get("project_id")

            # Extract event name from NATS subject by stripping prefix
            subject = msg.subject
            if subject.startswith(_SUBJECT_PREFIX):
                event_name = subject[len(_SUBJECT_PREFIX):]
            else:
                event_name = subject

            if project_id:
                await sio.emit(event_name, data, room=f"project:{project_id}")
            else:
                await sio.emit(event_name, data)

            await msg.ack()

            logger.debug(
                "Bridged event %s to room project:%s",
                event_name,
                project_id,
            )
        except Exception:
            logger.debug("Bridge loop error processing message", exc_info=True)
