"""Sous-package embedding : interface abstraite, providers concrets et factory."""

from core.embedding.base import BaseEmbeddingProvider
from core.embedding.factory import get_embedding_provider

__all__ = ["BaseEmbeddingProvider", "get_embedding_provider"]
