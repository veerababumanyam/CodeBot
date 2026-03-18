"""Tests for YAML graph definition loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from graph_engine.models.graph_def import GraphDefinition
from graph_engine.yaml.loader import load_graph_definition, load_graph_definition_from_string

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoadGraphDefinition:
    def test_loads_simple_pipeline(self):
        gd = load_graph_definition(FIXTURES / "simple_pipeline.yaml")
        assert isinstance(gd, GraphDefinition)
        assert gd.name == "simple-pipeline"
        assert len(gd.nodes) == 3
        assert gd.entry_nodes == ["analyzer"]

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_graph_definition(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml_syntax_raises_value_error(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("{ invalid: yaml: [")
        with pytest.raises(ValueError, match="YAML"):
            load_graph_definition(bad)

    def test_missing_required_field_raises_validation_error(self, tmp_path):
        no_name = tmp_path / "no_name.yaml"
        no_name.write_text(
            "nodes:\n  - id: a\n    type: agent\nedges: []\nentry_nodes: [a]\nexit_nodes: [a]\n"
        )
        with pytest.raises(ValidationError):
            load_graph_definition(no_name)

    def test_unknown_node_type_raises_validation_error(self, tmp_path):
        bad_type = tmp_path / "bad_type.yaml"
        bad_type.write_text(
            "name: t\nnodes:\n  - id: a\n    type: teleporter\n"
            "edges: []\nentry_nodes: [a]\nexit_nodes: [a]\n"
        )
        with pytest.raises(ValidationError):
            load_graph_definition(bad_type)


class TestLoadGraphDefinitionFromString:
    def test_loads_from_string(self):
        yaml_str = (FIXTURES / "simple_pipeline.yaml").read_text()
        gd = load_graph_definition_from_string(yaml_str)
        assert isinstance(gd, GraphDefinition)
        assert gd.name == "simple-pipeline"
