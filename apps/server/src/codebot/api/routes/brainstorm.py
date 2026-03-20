"""Brainstorm session endpoints for projects."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.deps import get_current_user, get_db, require_role
from codebot.api.envelope import ResponseEnvelope
from codebot.api.schemas.brainstorm import BrainstormRespondRequest, BrainstormSessionResponse
from codebot.db.models.user import User
from codebot.services.brainstorm_service import BrainstormService
from codebot.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/brainstorm", tags=["brainstorm"])


def _get_project_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectService:
    return ProjectService(db)


def _get_brainstorm_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrainstormService:
    return BrainstormService(db)


async def _get_owned_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(_get_project_service)],
):
    project = await service.get(project_id)
    if project is None or (
        project.user_id != current_user.id and current_user.role.value.lower() != "admin"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=ResponseEnvelope[BrainstormSessionResponse])
async def get_brainstorm_session(
    project=Depends(_get_owned_project),
    service: Annotated[BrainstormService, Depends(_get_brainstorm_service)] = None,
) -> ResponseEnvelope[BrainstormSessionResponse]:
    session = await service.get_session(project)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorm session not found",
        )
    return ResponseEnvelope(data=BrainstormSessionResponse.model_validate(session))


@router.post("/start", response_model=ResponseEnvelope[BrainstormSessionResponse])
async def start_brainstorm_session(
    project=Depends(_get_owned_project),
    _current_user: Annotated[User, Depends(require_role("user", "admin"))] = None,
    service: Annotated[BrainstormService, Depends(_get_brainstorm_service)] = None,
) -> ResponseEnvelope[BrainstormSessionResponse]:
    session = await service.start_session(project)
    return ResponseEnvelope(data=BrainstormSessionResponse.model_validate(session))


@router.post("/respond", response_model=ResponseEnvelope[BrainstormSessionResponse])
async def respond_to_brainstorm(
    body: BrainstormRespondRequest,
    project=Depends(_get_owned_project),
    _current_user: Annotated[User, Depends(require_role("user", "admin"))] = None,
    service: Annotated[BrainstormService, Depends(_get_brainstorm_service)] = None,
) -> ResponseEnvelope[BrainstormSessionResponse]:
    session = await service.respond(
        project,
        content=body.content,
        question_id=body.question_id,
    )
    return ResponseEnvelope(data=BrainstormSessionResponse.model_validate(session))


@router.post("/finalize", response_model=ResponseEnvelope[BrainstormSessionResponse])
async def finalize_brainstorm(
    project=Depends(_get_owned_project),
    _current_user: Annotated[User, Depends(require_role("user", "admin"))] = None,
    service: Annotated[BrainstormService, Depends(_get_brainstorm_service)] = None,
) -> ResponseEnvelope[BrainstormSessionResponse]:
    session = await service.finalize(project)
    return ResponseEnvelope(data=BrainstormSessionResponse.model_validate(session))