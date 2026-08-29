"""Sous-package vector_store : interface abstraite, provider Chroma et factory."""

from core.vector_store.base import BaseVectorStoreProvider, VectorDocument, VectorSearchResult
from core.vector_store.factory import get_vector_store_provider

__all__ = [
    "BaseVectorStoreProvider",
    "VectorDocument",
    "VectorSearchResult",
    "get_vector_store_provider",
]
