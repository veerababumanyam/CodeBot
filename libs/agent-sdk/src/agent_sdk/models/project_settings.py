"""Typed project settings schema with 8 categories.

Lives in agent-sdk so both server and graph-engine can import it
without circular dependencies (only depends on Pydantic).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class TechStackSettings(BaseModel):
    """Technology stack preferences for the project."""

    model_config = ConfigDict(extra="forbid")

    primary_language: str = "python"
    secondary_language: str = ""
    frontend_framework: str = ""
    backend_framework: str = "fastapi"
    css_framework: str = ""
    ui_component_library: str = ""
    database_primary: str = "postgresql"
    database_secondary: str = ""
    orm: str = "sqlalchemy"
    package_manager: str = "uv"
    monorepo_tool: str = ""
    runtime_version: str = ""
    test_framework: str = "pytest"
    linter: str = "ruff"
    formatter: str = "ruff"


class BrandingSettings(BaseModel):
    """Visual branding and identity preferences."""

    model_config = ConfigDict(extra="forbid")

    brand_name: str = ""
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#2563eb"
    secondary_color: str = "#7c3aed"
    accent_color: str = "#06b6d4"
    error_color: str = "#dc2626"
    warning_color: str = "#d97706"
    success_color: str = "#16a34a"
    font_heading: str = ""
    font_body: str = ""
    font_mono: str = ""
    border_radius: str = "md"


class UIUXSettings(BaseModel):
    """UI/UX design preferences."""

    model_config = ConfigDict(extra="forbid")

    design_system: str = ""
    theme_mode: str = "system"
    layout_strategy: str = "responsive"
    responsive_approach: str = "mobile-first"
    breakpoints: dict[str, int] = {}
    animation_preference: str = "subtle"
    density: str = "comfortable"
    icon_library: str = ""
    sidebar_style: str = "collapsible"
    form_validation: str = "inline"
    toast_position: str = "bottom-right"


class I18nSettings(BaseModel):
    """Internationalization and localization preferences."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    primary_locale: str = "en-US"
    supported_locales: list[str] = []
    rtl_support: bool = False
    date_format: str = "ISO"
    time_format: str = "24h"
    number_format: str = "standard"
    currency: str = "USD"
    i18n_framework: str = ""
    translation_strategy: str = "key-based"


class VisibilitySettings(BaseModel):
    """Project visibility and licensing preferences."""

    model_config = ConfigDict(extra="forbid")

    visibility: str = "private"
    license: str = ""
    open_source: bool = False
    readme_template: str = "standard"


class DeploymentSettings(BaseModel):
    """Deployment and hosting preferences."""

    model_config = ConfigDict(extra="forbid")

    hosting_provider: str = ""
    hosting_tier: str = ""
    environments: list[str] = ["development", "staging", "production"]
    domain: str = ""
    ssl_enabled: bool = True
    cdn_enabled: bool = False
    region: str = ""
    auto_deploy: bool = False


class PipelineSettings(BaseModel):
    """Pipeline execution preferences."""

    model_config = ConfigDict(extra="forbid")

    preset: str = "full"
    enable_tests: bool = True
    enable_security: bool = True
    enable_a11y: bool = True
    enable_performance: bool = False
    enable_i18n: bool = False
    approval_gates: list[str] = []
    llm_preference: str = ""
    cost_budget_usd: float | None = None
    token_budget: int | None = None


class AccessibilitySettings(BaseModel):
    """Accessibility compliance preferences."""

    model_config = ConfigDict(extra="forbid")

    wcag_level: str = "AA"
    color_contrast_mode: str = "standard"
    focus_management: bool = True
    skip_navigation: bool = True
    screen_reader_optimization: bool = True
    reduced_motion_support: bool = True
    keyboard_navigation: bool = True
    aria_landmarks: bool = True


class ProjectSettings(BaseModel):
    """Top-level project settings aggregating all 8 categories.

    Every field has sensible defaults — ``ProjectSettings()`` is always valid.
    Uses ``extra="forbid"`` to catch typos at the API boundary.
    """

    model_config = ConfigDict(extra="forbid")

    version: int = 1
    tech_stack: TechStackSettings = TechStackSettings()
    branding: BrandingSettings = BrandingSettings()
    ui_ux: UIUXSettings = UIUXSettings()
    i18n: I18nSettings = I18nSettings()
    visibility: VisibilitySettings = VisibilitySettings()
    deployment: DeploymentSettings = DeploymentSettings()
    pipeline: PipelineSettings = PipelineSettings()
    accessibility: AccessibilitySettings = AccessibilitySettings()
    custom: dict[str, Any] = {}

    @property
    def project_archetype(self) -> str:
        """Compute a short archetype string from tech stack + UI settings.

        Example: ``"python-fastapi-react-tailwind-postgresql"``
        """
        parts: list[str] = []
        ts = self.tech_stack
        if ts.primary_language:
            parts.append(ts.primary_language)
        if ts.backend_framework:
            parts.append(ts.backend_framework)
        if ts.frontend_framework:
            parts.append(ts.frontend_framework)
        if ts.css_framework:
            parts.append(ts.css_framework)
        if self.ui_ux.design_system:
            parts.append(self.ui_ux.design_system)
        if ts.database_primary:
            parts.append(ts.database_primary)
        return "-".join(parts) if parts else "default"
