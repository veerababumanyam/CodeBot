"""Project type detection and adaptive pipeline filtering.

Detects whether a project is greenfield, inflight, or brownfield based on
the repository state, then filters pipeline phases accordingly.
"""

from __future__ import annotations

from pathlib import Path

from agent_sdk.models.enums import ProjectType

from codebot.pipeline.models import PipelineConfig

# File extensions recognised as source code for project classification.
_SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".swift", ".rb"}
)

# Directories excluded from source-file counting.
_EXCLUDED_DIRS: frozenset[str] = frozenset({"node_modules", ".git", "__pycache__", ".venv", "venv"})

# Threshold: repositories with more source files than this are BROWNFIELD.
_BROWNFIELD_FILE_THRESHOLD: int = 50


def detect_project_type(
    repository_path: str,
    prd_content: str = "",
) -> ProjectType:
    """Detect whether a project is greenfield, inflight, or brownfield.

    Args:
        repository_path: Path to the project's git repository.  An empty
            string indicates no existing repository.
        prd_content: Optional PRD text that may contain an explicit
            ``project_type:`` hint.

    Returns:
        A :class:`ProjectType` enum value.

    Detection heuristics (applied in order):

    1. Explicit ``project_type: <type>`` in *prd_content* overrides all.
    2. No *repository_path* (empty string) -> ``GREENFIELD``.
    3. *repository_path* exists with ``.git`` and > 50 source files ->
       ``BROWNFIELD``.
    4. *repository_path* exists with ``.git`` and 1-50 source files ->
       ``INFLIGHT``.
    5. Fallback -> ``GREENFIELD``.
    """
    # 1. Explicit hints in PRD content
    prd_type = _extract_prd_type_hint(prd_content)
    if prd_type is not None:
        return prd_type

    # 2. No repo path -> brand new project
    if not repository_path:
        return ProjectType.GREENFIELD

    repo = Path(repository_path)
    if not repo.exists() or not (repo / ".git").exists():
        return ProjectType.GREENFIELD

    # 3-4. Count source files
    source_count = _count_source_files(repo)
    if source_count > _BROWNFIELD_FILE_THRESHOLD:
        return ProjectType.BROWNFIELD
    if source_count > 0:
        return ProjectType.INFLIGHT

    # 5. Fallback
    return ProjectType.GREENFIELD


def adapt_pipeline_for_project_type(
    config: PipelineConfig,
    project_type: ProjectType,
) -> PipelineConfig:
    """Filter pipeline phases based on project type.

    Phases whose :attr:`~codebot.pipeline.models.PhaseConfig.skip_for_project_types`
    list contains the project type's value (case-insensitive) are removed.

    Args:
        config: The full pipeline configuration.
        project_type: Detected or user-specified project type.

    Returns:
        A new :class:`PipelineConfig` with filtered phases.
    """
    type_value = project_type.value.lower()
    adapted_phases = [
        phase
        for phase in config.phases
        if type_value not in [t.lower() for t in phase.skip_for_project_types]
    ]
    return config.model_copy(update={"phases": adapted_phases})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_prd_type_hint(prd_content: str) -> ProjectType | None:
    """Extract an explicit ``project_type: <value>`` hint from PRD text."""
    if not prd_content:
        return None

    prd_lower = prd_content.lower()
    for member in ProjectType:
        needle = f"project_type: {member.value.lower()}"
        if needle in prd_lower:
            return member
    return None


def _count_source_files(repo: Path) -> int:
    """Count recognised source files, excluding common non-source directories."""
    count = 0
    for f in repo.rglob("*"):
        # Skip excluded directory trees
        if any(part in _EXCLUDED_DIRS for part in f.parts):
            continue
        if f.is_file() and f.suffix in _SOURCE_EXTENSIONS:
            count += 1
    return count
