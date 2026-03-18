"""Fallback chain management for the Multi-LLM abstraction layer.

Builds and configures LiteLLM Router instances with fallback chains
derived from the YAML configuration's routing table.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import litellm

if TYPE_CHECKING:
    from codebot.llm.config import LLMConfig
    from codebot.llm.providers import ProviderRegistry

logger = logging.getLogger(__name__)


class FallbackChainManager:
    """Manages fallback chain configuration for LiteLLM Router.

    Reads routing rules from LLMConfig and builds a LiteLLM Router
    with fallback mappings so that when a primary model fails on a
    server error, the request is automatically retried against the
    next model in the chain.

    Args:
        config: The LLMConfig containing routing rules and fallback settings.
        provider_registry: The ProviderRegistry for building model lists.
    """

    def __init__(self, config: LLMConfig, provider_registry: ProviderRegistry) -> None:
        self._config = config
        self._provider_registry = provider_registry

    def build_litellm_router(self) -> litellm.Router:
        """Build a configured LiteLLM Router with fallback chains.

        Creates the Router with:
        - Model list from ProviderRegistry
        - Fallback mappings from routing table
        - Retry and timeout settings from FallbackConfig

        Returns:
            A configured litellm.Router instance.
        """
        model_list = self._provider_registry.build_litellm_model_list()

        # Build deduplicated fallback mappings
        fallback_mapping = self.get_fallback_mapping()
        fallbacks = [
            {primary: fallback_models}
            for primary, fallback_models in fallback_mapping.items()
            if fallback_models
        ]

        router = litellm.Router(
            model_list=model_list,
            num_retries=self._config.fallback.num_retries,
            timeout=self._config.fallback.timeout_seconds,
            fallbacks=fallbacks,
            enable_pre_call_checks=True,
        )

        logger.info(
            "LiteLLM Router built with %d models, %d fallback chains",
            len(model_list),
            len(fallbacks),
        )
        return router

    def get_fallback_mapping(self) -> dict[str, list[str]]:
        """Build a deduplicated mapping of primary models to fallback models.

        When the same primary model appears in multiple routing rules,
        the fallback lists are merged (union) with order preserved.

        Returns:
            Dict mapping primary model names to ordered fallback model lists.
        """
        mapping: dict[str, list[str]] = {}

        for rule in self._config.routing_table.values():
            primary = rule.primary_model
            if primary not in mapping:
                mapping[primary] = []

            # Merge fallbacks, preserving order and avoiding duplicates
            for fallback in rule.fallback_models:
                if fallback not in mapping[primary]:
                    mapping[primary].append(fallback)

        return mapping
