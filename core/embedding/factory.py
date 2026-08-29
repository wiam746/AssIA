"""Factory de selection du provider d'embeddings. Provider disponible : Ollama (local)."""

from functools import lru_cache

from config.settings import settings
from core.embedding.base import BaseEmbeddingProvider
from core.embedding.provider import OllamaEmbeddingProvider

_PROVIDERS = {
    "ollama": OllamaEmbeddingProvider,
}


@lru_cache
def get_embedding_provider(provider_name: str = "") -> BaseEmbeddingProvider:
    """Retourne une instance (mise en cache) du provider d'embeddings configure (settings.embedding_provider par defaut)."""
    name = (provider_name or settings.embedding_provider).lower()

    if name not in _PROVIDERS:
        raise ValueError(
            f"Provider d'embeddings inconnu : '{name}'. Providers disponibles : {list(_PROVIDERS.keys())}"
        )

    return _PROVIDERS[name]()