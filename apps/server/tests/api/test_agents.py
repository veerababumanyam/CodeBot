"""Tests for agent management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.db.models.agent import Agent, AgentStatus, AgentType


async def _create_project(
    client: AsyncClient, headers: dict[str, str], name: str = "Agent Test Project"
) -> str:
    """Helper to create a project and return its ID."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def _insert_agent(
    db: AsyncSession,
    project_id: str,
    agent_type: AgentType = AgentType.BACKEND_DEV,
    status: AgentStatus = AgentStatus.IDLE,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
) -> Agent:
    """Insert an agent record directly into the DB."""
    from uuid import UUID

    agent = Agent(
        project_id=UUID(project_id),
        agent_type=agent_type,
        status=status,
        llm_provider=llm_provider,
        llm_model=llm_model,
        system_prompt_hash="abc123",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.mark.integration
class TestListAgents:
    """Tests for GET /api/v1/agents."""

    async def test_list_agents(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Listing agents with project_id filter returns matching agents."""
        project_id = await _create_project(async_client, auth_headers)
        await _insert_agent(test_db_session, project_id)

        response = await async_client.get(
            f"/api/v1/agents?project_id={project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    async def test_list_agents_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Filtering agents by status returns only matching agents."""
        project_id = await _create_project(async_client, auth_headers)
        await _insert_agent(test_db_session, project_id, status=AgentStatus.RUNNING)
        await _insert_agent(
            test_db_session,
            project_id,
            agent_type=AgentType.FRONTEND_DEV,
            status=AgentStatus.COMPLETED,
        )

        response = await async_client.get(
            f"/api/v1/agents?project_id={project_id}&status=running",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1


@pytest.mark.integration
class TestGetAgent:
    """Tests for GET /api/v1/agents/{id} and /api/v1/agents/types."""

    async def test_get_agent_detail(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Getting agent by ID returns detail including worktree_path."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(test_db_session, project_id)

        response = await async_client.get(
            f"/api/v1/agents/{agent.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "worktree_path" in data

    async def test_get_agent_types(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Getting agent types returns a non-empty list with expected fields."""
        response = await async_client.get(
            "/api/v1/agents/types",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "type" in first
        assert "display_name" in first
        assert "category" in first
        assert "capabilities" in first


@pytest.mark.integration
class TestAgentLifecycle:
    """Tests for agent start/stop/restart lifecycle endpoints."""

    async def test_start_agent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Starting an IDLE agent transitions it to running."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(test_db_session, project_id, status=AgentStatus.IDLE)

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "running"

    async def test_start_terminated_agent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Starting a TERMINATED agent transitions it to running."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.TERMINATED
        )

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "running"

    async def test_start_running_agent_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Starting an already-RUNNING agent returns 400."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.RUNNING
        )

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_stop_agent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Stopping a RUNNING agent transitions it to terminated."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.RUNNING
        )

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/stop",
            json={"reason": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "terminated"

    async def test_restart_agent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Restarting a TERMINATED agent transitions it to running."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.TERMINATED
        )

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/restart",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "running"

    async def test_stop_completed_agent_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Stopping a COMPLETED agent returns 400."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.COMPLETED
        )

        response = await async_client.post(
            f"/api/v1/agents/{agent.id}/stop",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestConfigureAgent:
    """Tests for PATCH /api/v1/agents/{id}/config."""

    async def test_configure_agent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Configuring an IDLE agent updates its model and provider."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(test_db_session, project_id, status=AgentStatus.IDLE)

        response = await async_client.patch(
            f"/api/v1/agents/{agent.id}/config",
            json={"llm_provider": "anthropic", "llm_model": "claude-3-opus"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["llm_provider"] == "anthropic"
        assert data["llm_model"] == "claude-3-opus"

    async def test_configure_running_agent_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Configuring a RUNNING agent returns 400."""
        project_id = await _create_project(async_client, auth_headers)
        agent = await _insert_agent(
            test_db_session, project_id, status=AgentStatus.RUNNING
        )

        response = await async_client.patch(
            f"/api/v1/agents/{agent.id}/config",
            json={"llm_model": "gpt-4"},
            headers=auth_headers,
        )
        assert response.status_code == 400
