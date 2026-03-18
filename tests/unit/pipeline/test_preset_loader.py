"""Tests for pipeline configuration models and YAML preset loader.

Covers PIPE-04: Pipeline configurations loadable from YAML presets.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from codebot.pipeline.models import (
    GateConfig,
    PhaseConfig,
    PipelineConfig,
    PipelineSettings,
)
from codebot.pipeline.loader import load_preset


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs" / "pipelines"


@pytest.fixture()
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory with a minimal valid preset."""
    preset = {
        "pipeline": {
            "name": "tmp-preset",
            "version": "1.0",
            "description": "A temporary preset",
            "phases": [
                {"name": "init", "agents": ["orchestrator"]},
            ],
        }
    }
    config_dir = tmp_path / "configs" / "pipelines"
    config_dir.mkdir(parents=True)
    (config_dir / "tmp-preset.yaml").write_text(yaml.dump(preset))
    return config_dir


# ---------------------------------------------------------------------------
# Test 1: load_preset("full") returns PipelineConfig with correct name/phases
# ---------------------------------------------------------------------------


def test_load_full_preset() -> None:
    config = load_preset("full", config_dir=CONFIGS_DIR)
    assert isinstance(config, PipelineConfig)
    assert config.name == "full-sdlc"
    # S0 through S10 = 11 phases total in full preset
    assert len(config.phases) == 11


# ---------------------------------------------------------------------------
# Test 2: load_preset("quick") returns fewer phases
# ---------------------------------------------------------------------------


def test_load_quick_preset() -> None:
    config = load_preset("quick", config_dir=CONFIGS_DIR)
    assert isinstance(config, PipelineConfig)
    assert config.name == "quick"
    # Quick skips brainstorm (S1), research (S2), document (S9)
    assert len(config.phases) < 11


# ---------------------------------------------------------------------------
# Test 3: load_preset("review-only") returns only QA phases
# ---------------------------------------------------------------------------


def test_load_review_only_preset() -> None:
    config = load_preset("review-only", config_dir=CONFIGS_DIR)
    assert isinstance(config, PipelineConfig)
    assert config.name == "review-only"
    # Should have very few phases (just QA-related)
    assert len(config.phases) <= 3


# ---------------------------------------------------------------------------
# Test 4: load_preset("nonexistent") raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_load_nonexistent_preset() -> None:
    with pytest.raises(FileNotFoundError, match="Pipeline preset not found"):
        load_preset("nonexistent", config_dir=CONFIGS_DIR)


# ---------------------------------------------------------------------------
# Test 5: PipelineConfig rejects empty phases list
# ---------------------------------------------------------------------------


def test_empty_phases_rejected() -> None:
    with pytest.raises(ValidationError, match="Pipeline must have at least one phase"):
        PipelineConfig(name="bad", version="1.0", phases=[])


# ---------------------------------------------------------------------------
# Test 6: PhaseConfig.parallel computed property
# ---------------------------------------------------------------------------


def test_parallel_property() -> None:
    phase_seq = PhaseConfig(name="seq", agents=["a"], sequential=True)
    assert phase_seq.parallel is False

    phase_par = PhaseConfig(name="par", agents=["a"], sequential=False)
    assert phase_par.parallel is True


# ---------------------------------------------------------------------------
# Test 7: GateConfig defaults
# ---------------------------------------------------------------------------


def test_gate_defaults() -> None:
    gate = GateConfig()
    assert gate.enabled is False
    assert gate.timeout_minutes == 30
    assert gate.timeout_action == "auto_approve"
    assert gate.mandatory is False
    assert gate.prompt == ""


# ---------------------------------------------------------------------------
# Test 8: PipelineSettings defaults
# ---------------------------------------------------------------------------


def test_settings_defaults() -> None:
    settings = PipelineSettings()
    assert settings.max_parallel_agents == 5
    assert settings.checkpoint_after_each_phase is True
    assert settings.cost_limit_usd == 50.0
    assert settings.timeout_minutes == 120


# ---------------------------------------------------------------------------
# Test 9: full.yaml has human gates on design and deliver phases
# ---------------------------------------------------------------------------


def test_full_preset_human_gates() -> None:
    config = load_preset("full", config_dir=CONFIGS_DIR)
    phase_map = {p.name: p for p in config.phases}

    design = phase_map["design"]
    assert design.human_gate.enabled is True

    deliver = phase_map["deliver"]
    assert deliver.human_gate.enabled is True


# ---------------------------------------------------------------------------
# Test 10: quick.yaml has all gates auto_approve
# ---------------------------------------------------------------------------


def test_quick_preset_gates_auto_approve() -> None:
    config = load_preset("quick", config_dir=CONFIGS_DIR)
    for phase in config.phases:
        if phase.human_gate.enabled:
            assert phase.human_gate.timeout_action == "auto_approve", (
                f"Phase {phase.name} gate timeout_action should be auto_approve"
            )


# ---------------------------------------------------------------------------
# Test: load_preset from tmp_path
# ---------------------------------------------------------------------------


def test_load_from_custom_dir(tmp_config_dir: Path) -> None:
    config = load_preset("tmp-preset", config_dir=tmp_config_dir)
    assert config.name == "tmp-preset"
    assert len(config.phases) == 1
