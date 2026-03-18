"""Tests for project type detection and adaptive pipeline filtering.

Covers PIPE-07: Pipeline detects project type and adapts stage configuration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_sdk.models.enums import ProjectType
from codebot.pipeline.loader import load_preset
from codebot.pipeline.models import PhaseConfig, PipelineConfig, PipelineSettings
from codebot.pipeline.project_detector import (
    adapt_pipeline_for_project_type,
    detect_project_type,
)


CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs" / "pipelines"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    phases: list[PhaseConfig],
    name: str = "test-pipeline",
) -> PipelineConfig:
    """Build a minimal PipelineConfig for testing."""
    return PipelineConfig(
        name=name,
        version="1.0",
        settings=PipelineSettings(),
        phases=phases,
    )


# ---------------------------------------------------------------------------
# Test 1: detect GREENFIELD when no repository path
# ---------------------------------------------------------------------------


def test_detect_greenfield_no_repo() -> None:
    result = detect_project_type(repository_path="")
    assert result == ProjectType.GREENFIELD


# ---------------------------------------------------------------------------
# Test 2: detect INFLIGHT for repo with recent commits and few source files
# ---------------------------------------------------------------------------


def test_detect_inflight(tmp_path: Path) -> None:
    # Create a git repo with a few source files (< 50)
    (tmp_path / ".git").mkdir()
    for i in range(10):
        (tmp_path / f"module_{i}.py").write_text(f"# module {i}")

    result = detect_project_type(repository_path=str(tmp_path))
    assert result == ProjectType.INFLIGHT


# ---------------------------------------------------------------------------
# Test 3: detect BROWNFIELD for repo with many existing source files
# ---------------------------------------------------------------------------


def test_detect_brownfield(tmp_path: Path) -> None:
    # Create a git repo with > 50 source files
    (tmp_path / ".git").mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    for i in range(60):
        (src_dir / f"module_{i}.py").write_text(f"# module {i}")

    result = detect_project_type(repository_path=str(tmp_path))
    assert result == ProjectType.BROWNFIELD


# ---------------------------------------------------------------------------
# Test 4: GREENFIELD adaptation returns all phases unchanged
# ---------------------------------------------------------------------------


def test_adapt_greenfield_unchanged() -> None:
    phases = [
        PhaseConfig(name="brainstorm", agents=["brainstorm"]),
        PhaseConfig(name="research", agents=["researcher"]),
        PhaseConfig(name="design", agents=["architect"]),
    ]
    config = _make_config(phases)

    adapted = adapt_pipeline_for_project_type(config, ProjectType.GREENFIELD)
    assert len(adapted.phases) == 3
    assert [p.name for p in adapted.phases] == ["brainstorm", "research", "design"]


# ---------------------------------------------------------------------------
# Test 5: INFLIGHT adaptation filters phases with "inflight" in skip list
# ---------------------------------------------------------------------------


def test_adapt_inflight_filters() -> None:
    phases = [
        PhaseConfig(
            name="brainstorm",
            agents=["brainstorm"],
            skip_for_project_types=["inflight", "brownfield"],
        ),
        PhaseConfig(name="design", agents=["architect"]),
        PhaseConfig(name="implement", agents=["dev"]),
    ]
    config = _make_config(phases)

    adapted = adapt_pipeline_for_project_type(config, ProjectType.INFLIGHT)
    assert len(adapted.phases) == 2
    assert "brainstorm" not in [p.name for p in adapted.phases]


# ---------------------------------------------------------------------------
# Test 6: BROWNFIELD adaptation filters phases with "brownfield" in skip list
# ---------------------------------------------------------------------------


def test_adapt_brownfield_filters() -> None:
    phases = [
        PhaseConfig(
            name="brainstorm",
            agents=["brainstorm"],
            skip_for_project_types=["brownfield"],
        ),
        PhaseConfig(
            name="research",
            agents=["researcher"],
            skip_for_project_types=["brownfield"],
        ),
        PhaseConfig(name="design", agents=["architect"]),
    ]
    config = _make_config(phases)

    adapted = adapt_pipeline_for_project_type(config, ProjectType.BROWNFIELD)
    assert len(adapted.phases) == 1
    assert adapted.phases[0].name == "design"


# ---------------------------------------------------------------------------
# Test 7: Full preset + BROWNFIELD skips brainstorm and research
# ---------------------------------------------------------------------------


def test_full_preset_brownfield_adaptation() -> None:
    config = load_preset("full", config_dir=CONFIGS_DIR)
    adapted = adapt_pipeline_for_project_type(config, ProjectType.BROWNFIELD)

    phase_names = [p.name for p in adapted.phases]
    assert "brainstorm" not in phase_names
    assert "research" not in phase_names
    # Other phases should still exist
    assert "design" in phase_names
    assert "implement" in phase_names
    assert "deliver" in phase_names


# ---------------------------------------------------------------------------
# Test 8: Quick preset + GREENFIELD returns unchanged (no skip entries match)
# ---------------------------------------------------------------------------


def test_quick_preset_greenfield_unchanged() -> None:
    config = load_preset("quick", config_dir=CONFIGS_DIR)
    adapted = adapt_pipeline_for_project_type(config, ProjectType.GREENFIELD)

    assert len(adapted.phases) == len(config.phases)
    assert [p.name for p in adapted.phases] == [p.name for p in config.phases]
