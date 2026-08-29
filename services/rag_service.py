"""
Service de RAG (Retrieval-Augmented Generation) generique.

Fournit une recherche de contexte pertinent dans le vector store, reutilisee
par les differents agents (chat, reunion, incident, ...) avant d'interroger
le LLM.
"""

import logging
from typing import Any, Dict, List, Optional

from core.document_processor import DocumentProcessor
from core.vector_store.base import BaseVectorStoreProvider, VectorDocument, VectorSearchResult
from core.vector_store.factory import get_vector_store_provider

logger = logging.getLogger("services.rag_service")


class RagService:
    """
    Orchestration du pipeline RAG : indexation de documents et recherche
    de contexte semantique pour alimenter les prompts envoyes au LLM.
    """

    def __init__(
        self,
        vector_store: Optional[BaseVectorStoreProvider] = None,
        document_processor: Optional[DocumentProcessor] = None,
    ) -> None:
        self.vector_store = vector_store or get_vector_store_provider()
        self.document_processor = document_processor or DocumentProcessor()

    async def index_document(
        self,
        file_path: str,
        *,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None,
    ) -> int:
        """
        Extrait le texte d'un fichier, le decoupe en chunks et les indexe
        dans le vector store. Retourne le nombre de chunks indexes.
        """
        chunks = self.document_processor.process(
            file_path, document_id=document_id, base_metadata=metadata
        )

        if not chunks:
            logger.warning("Aucun chunk genere pour le document '%s'.", document_id)
            return 0

        documents = [
            VectorDocument(id=chunk.chunk_id, text=chunk.text, metadata=chunk.metadata)
            for chunk in chunks
        ]

        await self.vector_store.add_documents(documents, collection=collection)
        logger.info("Document '%s' indexe (%d chunks).", document_id, len(documents))
        return len(documents)

    async def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[VectorSearchResult]:
        """Recherche les chunks les plus pertinents pour une requete donnee."""
        results = await self.vector_store.similarity_search(
            query, top_k=top_k, collection=collection, filters=filters
        )
        return [r for r in results if r.score >= min_score]

    async def retrieve_context_as_text(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[str]:
        """Comme `retrieve_context`, mais retourne directement des chaines pretes a etre injectees dans un prompt."""
        results = await self.retrieve_context(
            query, top_k=top_k, collection=collection, filters=filters, min_score=min_score
        )
        formatted = []
        for r in results:
            source = r.metadata.get("document_id", "document inconnu")
            formatted.append(f"[Source: {source}] {r.text}")
        return formatted

    async def remove_document(self, document_id: str, chunk_ids: List[str], collection: Optional[str] = None) -> None:
        """Supprime tous les chunks associes a un document du vector store."""
        await self.vector_store.delete_documents(chunk_ids, collection=collection)
        logger.info("Document '%s' retire du vector store (%d chunks).", document_id, len(chunk_ids))
