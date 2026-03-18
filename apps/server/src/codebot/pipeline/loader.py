"""YAML preset loader for pipeline configurations.

Reads a named YAML file from ``configs/pipelines/`` and validates it
through :class:`~codebot.pipeline.models.PipelineConfig`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from codebot.pipeline.models import PipelineConfig

# Default config directory resolved relative to this file's position in the
# repo tree:  apps/server/src/codebot/pipeline/loader.py  ->  repo root
_DEFAULT_CONFIG_DIR: Path = Path(__file__).resolve().parents[5] / "configs" / "pipelines"


def load_preset(
    preset_name: str,
    config_dir: Path | None = None,
) -> PipelineConfig:
    """Load and validate a pipeline preset from a YAML file.

    Args:
        preset_name: Name of the preset (without ``.yaml`` extension).
        config_dir: Directory containing preset YAML files.  Defaults to
            ``<repo>/configs/pipelines/``.

    Returns:
        A validated :class:`PipelineConfig` instance.

    Raises:
        FileNotFoundError: If the preset YAML file does not exist.
    """
    if config_dir is None:
        config_dir = _DEFAULT_CONFIG_DIR

    path = config_dir / f"{preset_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Pipeline preset not found: {path}")

    with open(path) as f:  # noqa: PTH123
        raw = yaml.safe_load(f)

    return PipelineConfig.model_validate(raw["pipeline"])
