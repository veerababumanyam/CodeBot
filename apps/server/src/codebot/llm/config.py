"""YAML-based configuration loading for the Multi-LLM abstraction layer.

Loads provider definitions, routing tables, budget limits, and fallback
settings from a YAML config file (default: ``configs/providers/llm.yaml``).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from codebot.llm.schemas import RoutingRule


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider/model.

    Attributes:
        model_name: Short name used in routing rules (e.g. "claude-sonnet").
        litellm_model: LiteLLM model identifier (e.g. "anthropic/claude-sonnet-4").
        api_key_env: Environment variable name holding the API key (None for local models).
        api_base: Base URL for self-hosted models (e.g. Ollama endpoint).
        enabled: Whether this provider is available for routing.
    """

    model_name: str
    litellm_model: str
    api_key_env: str | None = None
    api_base: str | None = None
    enabled: bool = True


class FallbackConfig(BaseModel):
    """Configuration for fallback behavior when providers fail.

    Attributes:
        num_retries: Number of retry attempts per provider.
        timeout_seconds: Timeout for a single LLM call.
        cooldown_seconds: How long to mark a provider unhealthy after failures.
    """

    num_retries: int = 3
    timeout_seconds: int = 60
    cooldown_seconds: int = 300


class BudgetConfig(BaseModel):
    """Budget limits for LLM spending.

    Attributes:
        global_budget_usd: Total budget across all agents in USD.
        warn_threshold: Fraction of budget that triggers a warning event (0.0-1.0).
        halt_threshold: Fraction of budget that halts further calls (0.0-1.0).
        agent_budgets: Per-agent budget overrides keyed by agent ID.
    """

    global_budget_usd: float = 50.0
    warn_threshold: float = 0.8
    halt_threshold: float = 0.95
    agent_budgets: dict[str, float] = {}


class LLMSettings(BaseModel):
    """General settings for LLM call behavior.

    Attributes:
        default_temperature: Default sampling temperature.
        default_max_tokens: Default maximum tokens for responses.
        enable_streaming: Whether streaming responses are enabled.
        enable_cost_tracking: Whether cost tracking is active.
    """

    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    enable_streaming: bool = True
    enable_cost_tracking: bool = True


class LLMConfig(BaseModel):
    """Root configuration for the LLM subsystem.

    Contains all provider definitions, routing rules, budget limits,
    fallback settings, and general LLM settings. Typically loaded
    from a YAML file via ``LLMConfig.from_yaml()``.

    Attributes:
        providers: List of available LLM provider configurations.
        routing_table: Maps task type names to routing rules.
        budget: Budget limits and thresholds.
        fallback: Fallback and retry configuration.
        settings: General LLM settings.
    """

    providers: list[ProviderConfig]
    routing_table: dict[str, RoutingRule]
    budget: BudgetConfig = BudgetConfig()
    fallback: FallbackConfig = FallbackConfig()
    settings: LLMSettings = LLMSettings()

    @classmethod
    def from_yaml(cls, path: str | Path) -> LLMConfig:
        """Load and validate an LLMConfig from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            A validated LLMConfig instance.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If the YAML content is invalid or fails validation.
        """
        path = Path(path)
        if not path.exists():
            msg = f"LLM config file not found: {path}"
            raise FileNotFoundError(msg)

        raw_text = path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            msg = f"Invalid YAML in {path}: {exc}"
            raise ValueError(msg) from exc

        if not isinstance(data, dict):
            msg = f"Invalid LLM config: expected a mapping, got {type(data).__name__}"
            raise ValueError(msg)

        try:
            return cls.model_validate(data)
        except Exception as exc:
            msg = f"Invalid LLM config in {path}: {exc}"
            raise ValueError(msg) from exc

    def get_enabled_providers(self) -> list[ProviderConfig]:
        """Return only providers that are enabled.

        Returns:
            List of ProviderConfig instances with enabled=True.
        """
        return [p for p in self.providers if p.enabled]

    def get_routing_rule(self, task_type: str) -> RoutingRule:
        """Look up the routing rule for a task type.

        If no rule is found for the given task type, returns a default
        rule using the first enabled provider.

        Args:
            task_type: The task type name (e.g. "ORCHESTRATION").

        Returns:
            The RoutingRule for the given task type, or a default rule.
        """
        if task_type in self.routing_table:
            return self.routing_table[task_type]

        # Default: use the first enabled provider
        enabled = self.get_enabled_providers()
        default_model = enabled[0].model_name if enabled else "unknown"
        return RoutingRule(
            primary_model=default_model,
            fallback_models=[],
            reason="Default routing (no rule defined for this task type)",
        )
