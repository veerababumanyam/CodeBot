"""Agent management and lifecycle endpoints for the CodeBot API."""

import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.deps import get_current_user, get_db, require_role
from codebot.api.envelope import PaginatedEnvelope, PaginationMeta, ResponseEnvelope
from codebot.api.schemas.agents import (
    AgentConfigUpdate,
    AgentDetailResponse,
    AgentResponse,
    AgentStopRequest,
    AgentTypeInfo,
)
from codebot.db.models.user import User
from codebot.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_agent_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentService:
    """Dependency that provides an AgentService instance."""
    return AgentService(db)


@router.get(
    "",
    response_model=PaginatedEnvelope[AgentResponse],
)
async def list_agents(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(_get_agent_service)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    project_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    agent_type: str | None = Query(default=None, alias="type"),
) -> PaginatedEnvelope[AgentResponse]:
    """List agents with optional filters.

    Args:
        current_user: Authenticated user.
        service: Agent service dependency.
        page: Page number (1-based).
        per_page: Items per page.
        project_id: Optional project filter.
        status_filter: Optional status filter.
        agent_type: Optional agent type filter.

    Returns:
        Paginated list of agents.
    """
    agents, total = await service.list_agents(
        page=page,
        per_page=per_page,
        project_id=project_id,
        status=status_filter,
        agent_type=agent_type,
    )
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    return PaginatedEnvelope(
        data=[AgentResponse.model_validate(a) for a in agents],
        pagination=PaginationMeta(
            page=page, per_page=per_page, total=total, total_pages=total_pages
        ),
    )


@router.get(
    "/types",
    response_model=ResponseEnvelope[list[AgentTypeInfo]],
)
async def get_agent_types(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[list[AgentTypeInfo]]:
    """Get all available agent types.

    Args:
        current_user: Authenticated user.
        service: Agent service dependency.

    Returns:
        List of agent type information.
    """
    types = await service.get_agent_types()
    return ResponseEnvelope(data=[AgentTypeInfo(**t) for t in types])


@router.get(
    "/{agent_id}",
    response_model=ResponseEnvelope[AgentDetailResponse],
)
async def get_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[AgentDetailResponse]:
    """Get an agent by ID with full detail.

    Args:
        agent_id: The agent UUID.
        current_user: Authenticated user.
        service: Agent service dependency.

    Returns:
        Agent detail wrapped in response envelope.
    """
    agent = await service.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return ResponseEnvelope(data=AgentDetailResponse.model_validate(agent))


@router.post(
    "/{agent_id}/start",
    response_model=ResponseEnvelope[AgentResponse],
)
async def start_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[AgentResponse]:
    """Start an agent (IDLE/TERMINATED -> RUNNING).

    Args:
        agent_id: The agent UUID.
        current_user: Authenticated user (user or admin role).
        service: Agent service dependency.

    Returns:
        Updated agent wrapped in response envelope.
    """
    agent = await service.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    updated = await service.start(agent)
    return ResponseEnvelope(data=AgentResponse.model_validate(updated))


@router.post(
    "/{agent_id}/stop",
    response_model=ResponseEnvelope[AgentResponse],
)
async def stop_agent(
    agent_id: UUID,
    body: AgentStopRequest,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[AgentResponse]:
    """Stop a running agent.

    Args:
        agent_id: The agent UUID.
        body: Stop request data (reason, force).
        current_user: Authenticated user (user or admin role).
        service: Agent service dependency.

    Returns:
        Updated agent wrapped in response envelope.
    """
    agent = await service.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    updated = await service.stop(agent, reason=body.reason, force=body.force)
    return ResponseEnvelope(data=AgentResponse.model_validate(updated))


@router.post(
    "/{agent_id}/restart",
    response_model=ResponseEnvelope[AgentResponse],
)
async def restart_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[AgentResponse]:
    """Restart an agent (TERMINATED/FAILED/COMPLETED -> RUNNING).

    Args:
        agent_id: The agent UUID.
        current_user: Authenticated user.
        service: Agent service dependency.

    Returns:
        Updated agent wrapped in response envelope.
    """
    agent = await service.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    updated = await service.restart(agent)
    return ResponseEnvelope(data=AgentResponse.model_validate(updated))


@router.patch(
    "/{agent_id}/config",
    response_model=ResponseEnvelope[AgentResponse],
)
async def configure_agent(
    agent_id: UUID,
    body: AgentConfigUpdate,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[AgentService, Depends(_get_agent_service)],
) -> ResponseEnvelope[AgentResponse]:
    """Update agent configuration (model, provider, etc.).

    Cannot be called while the agent is RUNNING.

    Args:
        agent_id: The agent UUID.
        body: Configuration update payload.
        current_user: Authenticated user (user or admin role).
        service: Agent service dependency.

    Returns:
        Updated agent wrapped in response envelope.
    """
    agent = await service.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    updated = await service.configure(agent, body)
    return ResponseEnvelope(data=AgentResponse.model_validate(updated))
