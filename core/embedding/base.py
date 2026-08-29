"""
Interface abstraite pour les providers d'embeddings.

Permet de generer des vecteurs a partir de texte independamment
du fournisseur utilise (OpenAI, modele local, ...).
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Interface que tout provider d'embeddings doit respecter."""

    provider_name: str = "base"
    dimensions: int = 0

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Genere le vecteur d'embedding pour un texte unique."""
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genere les vecteurs d'embedding pour un lot de textes."""
        raise NotImplementedError
