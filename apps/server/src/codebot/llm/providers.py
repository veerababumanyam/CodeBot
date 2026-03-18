"""Provider registry and health tracking for the Multi-LLM abstraction layer.

Manages provider configurations, tracks health status per provider,
and builds the model list that LiteLLM Router expects.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from pydantic import BaseModel

from codebot.llm.config import LLMConfig, ProviderConfig
from codebot.llm.exceptions import ModelNotFoundError


class ProviderHealth(BaseModel):
    """Tracks the health status of a single LLM provider.

    Attributes:
        name: Provider/model name.
        healthy: Whether the provider is currently considered healthy.
        last_error: Description of the most recent error, if any.
        consecutive_failures: Number of consecutive failed calls.
        last_checked: Timestamp of the last health check.
    """

    name: str
    healthy: bool = True
    last_error: str | None = None
    consecutive_failures: int = 0
    last_checked: datetime | None = None


# Number of consecutive failures before marking a provider unhealthy.
_UNHEALTHY_THRESHOLD = 3


class ProviderRegistry:
    """Registry of LLM providers with health tracking.

    Manages provider configurations loaded from LLMConfig, tracks
    health status per provider, and generates the model list format
    expected by LiteLLM Router.

    Args:
        config: The LLMConfig containing provider definitions.
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._providers: dict[str, ProviderConfig] = {
            p.model_name: p for p in config.providers
        }
        self._health: dict[str, ProviderHealth] = {
            p.model_name: ProviderHealth(name=p.model_name)
            for p in config.providers
        }

    def get_enabled_providers(self) -> list[ProviderConfig]:
        """Return only providers that are enabled.

        Returns:
            List of ProviderConfig instances with enabled=True.
        """
        return [p for p in self._config.providers if p.enabled]

    def get_provider(self, name: str) -> ProviderConfig:
        """Look up a provider by model name.

        Args:
            name: The model name to look up.

        Returns:
            The ProviderConfig for the given name.

        Raises:
            ModelNotFoundError: If no provider with the given name exists.
        """
        if name not in self._providers:
            raise ModelNotFoundError(model=name)
        return self._providers[name]

    def is_provider_healthy(self, name: str) -> bool:
        """Check whether a provider is currently healthy.

        A provider becomes unhealthy after ``_UNHEALTHY_THRESHOLD``
        consecutive failures.

        Args:
            name: The model name to check.

        Returns:
            True if the provider is healthy, False otherwise.
        """
        if name not in self._health:
            return False
        return self._health[name].healthy

    def record_failure(self, name: str, error: str) -> None:
        """Record a failed call to a provider.

        Increments the consecutive failure counter and marks the
        provider unhealthy if the threshold is reached.

        Args:
            name: The model name that failed.
            error: Description of the error.
        """
        if name not in self._health:
            return
        health = self._health[name]
        health.consecutive_failures += 1
        health.last_error = error
        health.last_checked = datetime.now(tz=timezone.utc)
        if health.consecutive_failures >= _UNHEALTHY_THRESHOLD:
            health.healthy = False

    def record_success(self, name: str) -> None:
        """Record a successful call to a provider.

        Resets the consecutive failure counter and marks the provider
        as healthy.

        Args:
            name: The model name that succeeded.
        """
        if name not in self._health:
            return
        health = self._health[name]
        health.consecutive_failures = 0
        health.healthy = True
        health.last_error = None
        health.last_checked = datetime.now(tz=timezone.utc)

    def build_litellm_model_list(self) -> list[dict[str, object]]:
        """Build the model list in the format expected by LiteLLM Router.

        Returns a list of dicts with ``model_name`` and ``litellm_params``
        for each enabled provider. The ``litellm_params`` dict contains
        the model identifier, optional API key (read from env), and
        optional API base URL.

        Returns:
            List of model configuration dicts for LiteLLM Router.
        """
        model_list: list[dict[str, object]] = []
        for provider in self.get_enabled_providers():
            litellm_params: dict[str, object] = {
                "model": provider.litellm_model,
            }

            if provider.api_key_env:
                api_key = os.getenv(provider.api_key_env)
                if api_key:
                    litellm_params["api_key"] = api_key

            if provider.api_base:
                litellm_params["api_base"] = provider.api_base

            model_list.append({
                "model_name": provider.model_name,
                "litellm_params": litellm_params,
            })

        return model_list
