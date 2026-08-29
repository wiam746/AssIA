"""Factory de selection du provider de vector store en fonction de la configuration (.env)."""

from functools import lru_cache

from config.settings import settings
from core.vector_store.base import BaseVectorStoreProvider
from core.vector_store.provider import ChromaVectorStoreProvider

_PROVIDERS = {
    "chroma": ChromaVectorStoreProvider,
}


@lru_cache
def get_vector_store_provider(provider_name: str | None = None) -> BaseVectorStoreProvider:
    """
    Retourne une instance (mise en cache) du provider de vector store demande.

    Args:
        provider_name: nom explicite du provider ("chroma" pour l'instant).
            Si non fourni, utilise VECTOR_STORE_PROVIDER depuis la configuration.
    """
    name = (provider_name or settings.vector_store_provider).lower()

    if name not in _PROVIDERS:
        raise ValueError(
            f"Provider de vector store inconnu : '{name}'. "
            f"Providers disponibles : {list(_PROVIDERS.keys())}"
        )

    provider_class = _PROVIDERS[name]
    return provider_class()
