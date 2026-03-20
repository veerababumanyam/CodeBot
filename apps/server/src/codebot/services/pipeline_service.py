"""Pipeline business logic, state transitions, and YAML preset loading."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import yaml
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from codebot.api.schemas.pipelines import PipelineCreate
from codebot.db.models.project import (
    PhaseStatus,
    PhaseType,
    Pipeline,
    PipelinePhase,
    PipelineStatus,
)

logger = logging.getLogger(__name__)

# In-memory fallback defaults used when YAML files are unavailable
_DEFAULT_PRESET_PHASES: dict[str, list[str]] = {
    "full": [
        "brainstorming",
        "planning",
        "research",
        "architecture",
        "design",
        "implementation",
        "review",
        "testing",
        "debug_fix",
        "documentation",
    ],
    "quick": ["planning", "implementation", "testing"],
    "review_only": ["review", "testing"],
}


def _load_preset_phases() -> dict[str, list[str]]:
    """Load pipeline presets from configs/pipelines/ YAML files.

    Tries to load full.yaml, quick.yaml, review_only.yaml. Each YAML
    file should have a ``pipeline.phases`` list with ``name`` keys. Falls
    back to ``_DEFAULT_PRESET_PHASES`` for any preset that cannot be loaded.

    Returns:
        Mapping of preset name to phase name list.
    """
    result = dict(_DEFAULT_PRESET_PHASES)

    # Resolve configs/pipelines/ relative to project root
    config_dir = Path(__file__).resolve().parents[4] / "configs" / "pipelines"

    file_map = {
        "full": "full.yaml",
        "quick": "quick.yaml",
        "review_only": "review-only.yaml",
    }

    for preset_name, filename in file_map.items():
        yaml_path = config_dir / filename
        try:
            if yaml_path.exists():
                with yaml_path.open() as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    # YAML structure: pipeline.phases[].name
                    pipeline_data = data.get("pipeline", data)
                    phases_data = pipeline_data.get("phases", [])
                    if isinstance(phases_data, list) and phases_data:
                        phase_names = []
                        for phase in phases_data:
                            if isinstance(phase, dict) and "name" in phase:
                                phase_names.append(phase["name"])
                            elif isinstance(phase, str):
                                phase_names.append(phase)
                        if phase_names:
                            result[preset_name] = phase_names
                            logger.debug(
                                "Loaded preset '%s' from %s: %s",
                                preset_name,
                                yaml_path,
                                phase_names,
                            )
        except Exception:
            logger.debug(
                "Failed to load preset '%s' from %s, using defaults",
                preset_name,
                yaml_path,
                exc_info=True,
            )

    return result


class PipelineService:
    """Business logic for pipeline operations.

    Args:
        db: Async database session.
    """

    # Valid state transitions for pipeline lifecycle
    VALID_TRANSITIONS: dict[PipelineStatus, list[PipelineStatus]] = {
        PipelineStatus.PENDING: [PipelineStatus.RUNNING, PipelineStatus.CANCELLED],
        PipelineStatus.RUNNING: [
            PipelineStatus.PAUSED,
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        ],
        PipelineStatus.PAUSED: [PipelineStatus.RUNNING, PipelineStatus.CANCELLED],
        # Terminal states -- no transitions allowed
        PipelineStatus.COMPLETED: [],
        PipelineStatus.FAILED: [],
        PipelineStatus.CANCELLED: [],
    }

    DEFAULT_PRESET_PHASES = _DEFAULT_PRESET_PHASES

    # Map phase name strings to PhaseType enum values
    PHASE_NAME_TO_TYPE: dict[str, PhaseType] = {
        "brainstorming": PhaseType.BRAINSTORMING,
        "planning": PhaseType.PLANNING,
        "research": PhaseType.RESEARCH,
        "architecture": PhaseType.ARCHITECTURE,
        "design": PhaseType.DESIGN,
        "implementation": PhaseType.IMPLEMENTATION,
        "review": PhaseType.REVIEW,
        "testing": PhaseType.TESTING,
        "debug_fix": PhaseType.DEBUG_FIX,
        "documentation": PhaseType.DOCUMENTATION,
        "deployment": PhaseType.DEPLOYMENT,
        "delivery": PhaseType.DELIVERY,
    }

    @staticmethod
    def load_preset_phases() -> dict[str, list[str]]:
        """Load pipeline presets from configs/pipelines/ YAML files.

        Delegates to module-level ``_load_preset_phases``.
        """
        return _load_preset_phases()

    # Load presets once at class definition time
    PRESET_PHASES: dict[str, list[str]] = _load_preset_phases()

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, project_id: UUID, payload: PipelineCreate) -> Pipeline:
        """Create a new pipeline with phases based on preset or custom list.

        Args:
            project_id: The owning project's UUID.
            payload: Pipeline creation data.

        Returns:
            The created Pipeline ORM object with phases.
        """
        pipeline = Pipeline(
            project_id=project_id,
            status=PipelineStatus.PENDING,
            graph_definition={"mode": payload.mode, "config": payload.config},
        )
        self._db.add(pipeline)
        await self._db.flush()

        # Determine phase list
        phase_names = payload.phases if payload.phases else self.PRESET_PHASES.get(
            payload.mode, self.DEFAULT_PRESET_PHASES["full"]
        )

        for idx, phase_name in enumerate(phase_names):
            phase_type = self.PHASE_NAME_TO_TYPE.get(phase_name, PhaseType.IMPLEMENTATION)
            phase = PipelinePhase(
                pipeline_id=pipeline.id,
                name=phase_name,
                phase_type=phase_type,
                status=PhaseStatus.PENDING,
                order=idx,
            )
            self._db.add(phase)

        await self._db.commit()
        await self._db.refresh(pipeline)
        return pipeline

    async def get(self, pipeline_id: UUID) -> Pipeline | None:
        """Get a pipeline by ID.

        Args:
            pipeline_id: The pipeline's UUID.

        Returns:
            The Pipeline if found, else None.
        """
        return await self._db.get(Pipeline, pipeline_id)

    async def get_with_phases(self, pipeline_id: UUID) -> Pipeline | None:
        """Get a pipeline by ID with eager-loaded phases.

        Args:
            pipeline_id: The pipeline's UUID.

        Returns:
            The Pipeline with phases loaded, or None.
        """
        result = await self._db.execute(
            select(Pipeline)
            .where(Pipeline.id == pipeline_id)
            .options(selectinload(Pipeline.phases))
        )
        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        project_id: UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> tuple[list[Pipeline], int]:
        """List pipelines for a project with optional status filter.

        Args:
            project_id: The owning project's UUID.
            page: Page number (1-based).
            per_page: Items per page.
            status: Optional status filter (case-insensitive).

        Returns:
            Tuple of (pipelines list, total count).
        """
        query = select(Pipeline).where(Pipeline.project_id == project_id)
        count_query = (
            select(func.count()).select_from(Pipeline).where(Pipeline.project_id == project_id)
        )

        if status is not None:
            try:
                status_enum = PipelineStatus(status.upper())
            except ValueError:
                status_enum = None
            if status_enum is not None:
                query = query.where(Pipeline.status == status_enum)
                count_query = count_query.where(Pipeline.status == status_enum)

        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        result = await self._db.execute(query)
        pipelines = list(result.scalars().all())

        return pipelines, int(total)

    async def transition(
        self, pipeline: Pipeline, target_status: PipelineStatus
    ) -> Pipeline:
        """Transition a pipeline to a new status.

        Validates the transition against VALID_TRANSITIONS.

        Args:
            pipeline: The Pipeline ORM object.
            target_status: The target PipelineStatus.

        Returns:
            The updated Pipeline.

        Raises:
            HTTPException: 400 if the transition is invalid.
        """
        allowed = self.VALID_TRANSITIONS.get(pipeline.status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {pipeline.status.value} to {target_status.value}",
            )

        pipeline.status = target_status

        if target_status == PipelineStatus.RUNNING and pipeline.started_at is None:
            pipeline.started_at = datetime.now(UTC)

        if target_status in (
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        ):
            pipeline.completed_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(pipeline)
        return pipeline

    async def get_phases(self, pipeline_id: UUID) -> list[PipelinePhase]:
        """Get all phases for a pipeline ordered by phase order.

        Args:
            pipeline_id: The pipeline's UUID.

        Returns:
            Ordered list of PipelinePhase objects.
        """
        result = await self._db.execute(
            select(PipelinePhase)
            .where(PipelinePhase.pipeline_id == pipeline_id)
            .order_by(PipelinePhase.order)
        )
        return list(result.scalars().all())

    async def approve_phase(
        self,
        phase: PipelinePhase,
        approved_by: str,
        comment: str | None,
    ) -> PipelinePhase:
        """Approve a pipeline phase that is waiting for approval.

        Args:
            phase: The PipelinePhase ORM object.
            approved_by: Name/email of the approver.
            comment: Optional approval comment.

        Returns:
            The updated PipelinePhase.

        Raises:
            HTTPException: 400 if phase is not in WAITING_APPROVAL status.
        """
        if phase.status != PhaseStatus.WAITING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail=f"Phase is in {phase.status.value} state, not WAITING_APPROVAL",
            )

        phase.status = PhaseStatus.COMPLETED
        phase.approved_by = approved_by
        phase.completed_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(phase)
        return phase
