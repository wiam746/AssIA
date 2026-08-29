"""
Interface abstraite pour les vector stores.

Permet d'indexer et de rechercher des documents par similarite
semantique, independamment du moteur utilise (Chroma, autre...).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VectorDocument:
    """Un document (ou chunk de document) a indexer dans le vector store."""

    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchResult:
    """Un resultat de recherche par similarite dans le vector store."""

    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseVectorStoreProvider(ABC):
    """Interface que tout provider de vector store doit respecter."""

    provider_name: str = "base"

    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument], collection: Optional[str] = None) -> None:
        """Indexe une liste de documents (avec ou sans embeddings precalcules)."""
        raise NotImplementedError

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Recherche les documents les plus proches semantiquement d'une requete."""
        raise NotImplementedError

    @abstractmethod
    async def delete_documents(self, ids: List[str], collection: Optional[str] = None) -> None:
        """Supprime des documents du vector store par identifiant."""
        raise NotImplementedError

    @abstractmethod
    async def delete_collection(self, collection: Optional[str] = None) -> None:
        """Supprime entierement une collection."""
        raise NotImplementedError
