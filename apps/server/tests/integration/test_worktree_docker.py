"""Integration tests for Docker Compose worktree template.

Tests verify the YAML template is valid, uses correct port variables,
and includes healthchecks. These are YAML parsing tests, not Docker
runtime tests.
"""

from __future__ import annotations

import os

import pytest
import yaml


DOCKER_COMPOSE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "configs",
    "worktree",
    "docker-compose.worktree.yml",
)


@pytest.mark.integration
class TestDockerComposeTemplate:
    """Tests for the per-worktree Docker Compose template."""

    def test_docker_compose_template_is_valid_yaml(self) -> None:
        """The template parses as valid YAML with expected services."""
        with open(DOCKER_COMPOSE_PATH) as f:
            data = yaml.safe_load(f)

        assert "services" in data
        services = data["services"]
        assert "worktree-db" in services
        assert "worktree-redis" in services
        assert "worktree-app" in services

    def test_docker_compose_uses_port_vars(self) -> None:
        """Port configuration uses PORT_* environment variable references."""
        with open(DOCKER_COMPOSE_PATH) as f:
            content = f.read()

        assert "PORT_DB" in content
        assert "PORT_REDIS" in content
        assert "PORT_WEB" in content
        assert "PORT_API" in content

    def test_docker_compose_has_healthchecks(self) -> None:
        """Database and Redis services have healthcheck configurations."""
        with open(DOCKER_COMPOSE_PATH) as f:
            data = yaml.safe_load(f)

        services = data["services"]
        assert "healthcheck" in services["worktree-db"]
        assert "healthcheck" in services["worktree-redis"]
