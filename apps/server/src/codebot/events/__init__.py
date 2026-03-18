"""NATS JetStream event bus module for CodeBot inter-agent messaging."""

from codebot.events.bus import EventBus, create_event_bus, publish_event

__all__ = ["EventBus", "create_event_bus", "publish_event"]
