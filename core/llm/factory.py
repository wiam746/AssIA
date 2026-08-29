"""Factory de selection du provider LLM. Provider disponible : Ollama (local)."""

from functools import lru_cache

from config.settings import settings
from core.llm.base import BaseLLMProvider
from core.llm.provider import OllamaProvider

_PROVIDERS = {
    "ollama": OllamaProvider,
}


@lru_cache
def get_llm_provider(provider_name: str = "") -> BaseLLMProvider:
    """Retourne une instance (mise en cache) du provider LLM configure (settings.llm_provider par defaut)."""
    name = (provider_name or settings.llm_provider).lower()

    if name not in _PROVIDERS:
        raise ValueError(
            f"Provider LLM inconnu : '{name}'. Providers disponibles : {list(_PROVIDERS.keys())}"
        )

    return _PROVIDERS[name]()