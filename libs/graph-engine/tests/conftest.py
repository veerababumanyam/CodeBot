"""Shared fixtures for graph-engine tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def sample_node_def() -> dict:
    """A valid NodeDefinition as a raw dict."""
    return {
        "id": "analyzer",
        "type": "agent",
        "config": {"agent_type": "RESEARCHER"},
        "timeout_seconds": 300,
    }


@pytest.fixture()
def sample_edge_def() -> dict:
    """A valid EdgeDefinition as a raw dict."""
    return {
        "source": "analyzer",
        "target": "builder",
        "type": "state_flow",
    }


@pytest.fixture()
def sample_graph_def() -> dict:
    """A complete valid GraphDefinition as a raw dict."""
    return {
        "name": "test-pipeline",
        "version": "1.0",
        "description": "Test pipeline",
        "nodes": [
            {
                "id": "analyzer",
                "type": "agent",
                "config": {"agent_type": "RESEARCHER"},
                "timeout_seconds": 300,
            },
            {
                "id": "builder",
                "type": "agent",
                "config": {"agent_type": "BACKEND_DEV"},
                "timeout_seconds": 600,
            },
            {
                "id": "reviewer",
                "type": "agent",
                "config": {"agent_type": "CODE_REVIEWER"},
                "timeout_seconds": 300,
            },
        ],
        "edges": [
            {"source": "analyzer", "target": "builder", "type": "state_flow"},
            {"source": "builder", "target": "reviewer", "type": "state_flow"},
        ],
        "entry_nodes": ["analyzer"],
        "exit_nodes": ["reviewer"],
    }
