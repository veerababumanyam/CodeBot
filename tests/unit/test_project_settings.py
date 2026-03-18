"""Unit tests for the ProjectSettings Pydantic schema."""

from __future__ import annotations

import pytest
from agent_sdk.models.project_settings import (
    AccessibilitySettings,
    BrandingSettings,
    DeploymentSettings,
    I18nSettings,
    PipelineSettings,
    ProjectSettings,
    TechStackSettings,
    UIUXSettings,
    VisibilitySettings,
)
from pydantic import ValidationError


class TestProjectSettingsDefaults:
    """ProjectSettings() produces valid defaults for all 8 categories."""

    def test_default_construction_is_valid(self):
        ps = ProjectSettings()
        assert ps.version == 1
        assert isinstance(ps.tech_stack, TechStackSettings)
        assert isinstance(ps.branding, BrandingSettings)
        assert isinstance(ps.ui_ux, UIUXSettings)
        assert isinstance(ps.i18n, I18nSettings)
        assert isinstance(ps.visibility, VisibilitySettings)
        assert isinstance(ps.deployment, DeploymentSettings)
        assert isinstance(ps.pipeline, PipelineSettings)
        assert isinstance(ps.accessibility, AccessibilitySettings)
        assert ps.custom == {}

    def test_default_tech_stack_values(self):
        ps = ProjectSettings()
        assert ps.tech_stack.primary_language == "python"
        assert ps.tech_stack.backend_framework == "fastapi"
        assert ps.tech_stack.database_primary == "postgresql"
        assert ps.tech_stack.orm == "sqlalchemy"
        assert ps.tech_stack.package_manager == "uv"

    def test_default_pipeline_values(self):
        ps = ProjectSettings()
        assert ps.pipeline.preset == "full"
        assert ps.pipeline.enable_tests is True
        assert ps.pipeline.enable_security is True
        assert ps.pipeline.cost_budget_usd is None

    def test_default_accessibility_values(self):
        ps = ProjectSettings()
        assert ps.accessibility.wcag_level == "AA"
        assert ps.accessibility.keyboard_navigation is True

    def test_default_deployment_environments(self):
        ps = ProjectSettings()
        assert ps.deployment.environments == ["development", "staging", "production"]
        assert ps.deployment.ssl_enabled is True


class TestExtraForbid:
    """extra='forbid' rejects unknown keys on all sub-models."""

    def test_tech_stack_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            TechStackSettings(typo_field="x")

    def test_branding_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            BrandingSettings(brand_colour="red")

    def test_ui_ux_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            UIUXSettings(theme="dark")

    def test_i18n_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            I18nSettings(default_locale="en")

    def test_visibility_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            VisibilitySettings(is_public=True)

    def test_deployment_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            DeploymentSettings(provider="aws")

    def test_pipeline_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            PipelineSettings(mode="fast")

    def test_accessibility_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            AccessibilitySettings(wcag="AAA")

    def test_root_rejects_unknown_key(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ProjectSettings(theme="dark")


class TestPartialConstruction:
    """Partial construction fills remaining fields with defaults."""

    def test_partial_tech_stack(self):
        ps = ProjectSettings(
            tech_stack={"primary_language": "typescript", "frontend_framework": "react"}
        )
        assert ps.tech_stack.primary_language == "typescript"
        assert ps.tech_stack.frontend_framework == "react"
        # Defaults preserved
        assert ps.tech_stack.backend_framework == "fastapi"
        assert ps.tech_stack.database_primary == "postgresql"

    def test_partial_branding(self):
        ps = ProjectSettings(branding={"brand_name": "MyApp", "primary_color": "#ff0000"})
        assert ps.branding.brand_name == "MyApp"
        assert ps.branding.primary_color == "#ff0000"
        # Defaults preserved
        assert ps.branding.secondary_color == "#7c3aed"

    def test_partial_i18n(self):
        ps = ProjectSettings(
            i18n={"enabled": True, "supported_locales": ["en-US", "fr-FR", "de-DE"]}
        )
        assert ps.i18n.enabled is True
        assert len(ps.i18n.supported_locales) == 3
        assert ps.i18n.primary_locale == "en-US"

    def test_empty_dict_uses_all_defaults(self):
        ps = ProjectSettings(tech_stack={})
        assert ps.tech_stack == TechStackSettings()


class TestSerializationRoundTrip:
    """model_dump() -> model_validate() produces identical object."""

    def test_default_round_trip(self):
        ps = ProjectSettings()
        data = ps.model_dump(mode="json")
        ps2 = ProjectSettings.model_validate(data)
        assert ps == ps2

    def test_customized_round_trip(self):
        ps = ProjectSettings(
            tech_stack={"primary_language": "typescript", "frontend_framework": "react"},
            branding={"brand_name": "TestApp", "primary_color": "#123456"},
            i18n={"enabled": True, "supported_locales": ["en", "fr"]},
            pipeline={"preset": "quick", "cost_budget_usd": 50.0},
            custom={"extra_key": "value"},
        )
        data = ps.model_dump(mode="json")
        ps2 = ProjectSettings.model_validate(data)
        assert ps == ps2

    def test_json_mode_produces_serializable_types(self):
        ps = ProjectSettings()
        data = ps.model_dump(mode="json")
        # All values should be JSON-native types
        assert isinstance(data["version"], int)
        assert isinstance(data["tech_stack"], dict)
        assert isinstance(data["custom"], dict)


class TestDeepMerge:
    """Merging a settings patch into existing settings produces correct result."""

    def test_merge_tech_stack_patch(self):
        base = ProjectSettings()
        patch_data = base.model_dump(mode="json")
        patch_data["tech_stack"]["primary_language"] = "go"
        patch_data["tech_stack"]["frontend_framework"] = "svelte"
        merged = ProjectSettings.model_validate(patch_data)
        assert merged.tech_stack.primary_language == "go"
        assert merged.tech_stack.frontend_framework == "svelte"
        # Unpatched values preserved
        assert merged.tech_stack.database_primary == "postgresql"

    def test_merge_multiple_categories(self):
        base = ProjectSettings()
        data = base.model_dump(mode="json")
        data["branding"]["brand_name"] = "PatchedApp"
        data["pipeline"]["preset"] = "quick"
        merged = ProjectSettings.model_validate(data)
        assert merged.branding.brand_name == "PatchedApp"
        assert merged.pipeline.preset == "quick"
        # Other categories unchanged
        assert merged.tech_stack == TechStackSettings()


class TestProjectArchetype:
    """project_archetype computation from tech stack + ui_ux settings."""

    def test_default_archetype(self):
        ps = ProjectSettings()
        assert ps.project_archetype == "python-fastapi-postgresql"

    def test_full_stack_archetype(self):
        ps = ProjectSettings(
            tech_stack={
                "primary_language": "typescript",
                "backend_framework": "express",
                "frontend_framework": "react",
                "css_framework": "tailwind",
                "database_primary": "mongodb",
            },
            ui_ux={"design_system": "shadcn"},
        )
        assert ps.project_archetype == "typescript-express-react-tailwind-shadcn-mongodb"

    def test_minimal_archetype(self):
        ps = ProjectSettings(
            tech_stack={
                "primary_language": "",
                "backend_framework": "",
                "frontend_framework": "",
                "css_framework": "",
                "database_primary": "",
            }
        )
        assert ps.project_archetype == "default"

    def test_frontend_only_archetype(self):
        ps = ProjectSettings(
            tech_stack={
                "primary_language": "typescript",
                "backend_framework": "",
                "frontend_framework": "vue",
                "css_framework": "tailwind",
                "database_primary": "",
            }
        )
        assert ps.project_archetype == "typescript-vue-tailwind"


class TestSharedStateIntegration:
    """SharedState includes project_settings key.

    Note: Imports state.py directly via importlib.util to avoid
    graph_engine.__init__ pulling in langgraph (heavy optional dep).
    The graph-engine's own test suite handles full integration.
    """

    @pytest.fixture(autouse=True)
    def _import_state(self):
        """Load state.py as a standalone module (bypass package __init__)."""
        import importlib.util
        import pathlib

        state_path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "libs"
            / "graph-engine"
            / "src"
            / "graph_engine"
            / "models"
            / "state.py"
        )
        spec = importlib.util.spec_from_file_location("_state_standalone", state_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.state_mod = mod

    def test_shared_state_has_project_settings_annotation(self):
        assert "project_settings" in self.state_mod.SharedState.__annotations__

    def test_merge_dicts_reducer_works_for_settings(self):
        merge_dicts = self.state_mod.merge_dicts
        existing = {"tech_stack": {"primary_language": "python"}}
        update = {"branding": {"brand_name": "NewApp"}}
        result = merge_dicts(existing, update)
        assert result == {
            "tech_stack": {"primary_language": "python"},
            "branding": {"brand_name": "NewApp"},
        }


class TestL0ContextSettings:
    """L0Context accepts settings fields and role-based filtering works."""

    def test_l0_context_accepts_settings_fields(self):
        from codebot.context.models import L0Context

        ctx = L0Context(
            project_name="test",
            project_description="desc",
            tech_stack=["python"],
            conventions="pep8",
            pipeline_phase="S0",
            agent_system_prompt="You are...",
            branding={"brand_name": "MyApp"},
            ui_ux={"theme_mode": "dark"},
            accessibility={"wcag_level": "AAA"},
            project_archetype="python-fastapi-postgresql",
        )
        assert ctx.branding == {"brand_name": "MyApp"}
        assert ctx.ui_ux == {"theme_mode": "dark"}
        assert ctx.accessibility == {"wcag_level": "AAA"}
        assert ctx.project_archetype == "python-fastapi-postgresql"

    def test_l0_context_settings_default_to_empty(self):
        from codebot.context.models import L0Context

        ctx = L0Context(
            project_name="test",
            project_description="desc",
            tech_stack=["python"],
            conventions="",
            pipeline_phase="S0",
            agent_system_prompt="",
        )
        assert ctx.branding == {}
        assert ctx.ui_ux == {}
        assert ctx.i18n == {}
        assert ctx.visibility == {}
        assert ctx.deployment == {}
        assert ctx.pipeline_settings == {}
        assert ctx.accessibility == {}
        assert ctx.project_archetype == ""

    def test_settings_relevance_map_coverage(self):
        from codebot.context.models import SETTINGS_RELEVANCE

        # All keys should be agent type strings
        assert "FRONTEND_DEV" in SETTINGS_RELEVANCE
        assert "BACKEND_DEV" in SETTINGS_RELEVANCE
        assert "DESIGNER" in SETTINGS_RELEVANCE
        assert "ORCHESTRATOR" in SETTINGS_RELEVANCE
        assert "DEFAULT" in SETTINGS_RELEVANCE

        # Frontend devs get the most categories
        frontend_cats = SETTINGS_RELEVANCE["FRONTEND_DEV"]
        assert "tech_stack" in frontend_cats
        assert "branding" in frontend_cats
        assert "accessibility" in frontend_cats

        # Backend devs get fewer
        backend_cats = SETTINGS_RELEVANCE["BACKEND_DEV"]
        assert "tech_stack" in backend_cats
        assert "branding" not in backend_cats

    def test_settings_relevance_all_values_are_valid_categories(self):
        from codebot.context.models import SETTINGS_RELEVANCE

        valid_categories = {
            "tech_stack", "branding", "ui_ux", "i18n",
            "visibility", "deployment", "pipeline_settings", "accessibility",
        }
        for role, categories in SETTINGS_RELEVANCE.items():
            for cat in categories:
                assert cat in valid_categories, f"{role} references invalid category: {cat}"
