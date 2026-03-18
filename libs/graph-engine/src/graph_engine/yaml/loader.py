"""YAML loader for graph definitions."""

from __future__ import annotations

from pathlib import Path

import yaml

from graph_engine.models.graph_def import GraphDefinition


def load_graph_definition(path: str | Path) -> GraphDefinition:
    """Load and validate a graph definition from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Validated GraphDefinition.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid YAML syntax.
        pydantic.ValidationError: If the parsed data fails schema validation.
    """
    path = Path(path)
    if not path.exists():
        msg = f"Graph definition file not found: {path}"
        raise FileNotFoundError(msg)

    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        msg = f"YAML parse error in {path}: {e}"
        raise ValueError(msg) from e

    return GraphDefinition.model_validate(data)


def load_graph_definition_from_string(yaml_string: str) -> GraphDefinition:
    """Load and validate a graph definition from a YAML string.

    Args:
        yaml_string: YAML content as a string.

    Returns:
        Validated GraphDefinition.

    Raises:
        ValueError: If the string contains invalid YAML syntax.
        pydantic.ValidationError: If the parsed data fails schema validation.
    """
    try:
        data = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        msg = f"YAML parse error: {e}"
        raise ValueError(msg) from e

    return GraphDefinition.model_validate(data)
