"""
Implementation concrete du vector store base sur ChromaDB (persiste sur disque).
"""

from typing import Any, Dict, List, Optional

from config.settings import settings
from core.embedding.base import BaseEmbeddingProvider
from core.embedding.factory import get_embedding_provider
from core.vector_store.base import BaseVectorStoreProvider, VectorDocument, VectorSearchResult


class ChromaVectorStoreProvider(BaseVectorStoreProvider):
    """Provider de vector store base sur ChromaDB, avec persistance locale."""

    provider_name = "chroma"

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        default_collection: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir or settings.chroma_persist_dir)
        self._default_collection = default_collection or settings.chroma_collection_name
        self._embedding_provider = embedding_provider or get_embedding_provider()

    def _get_collection(self, collection: Optional[str] = None):
        name = collection or self._default_collection
        return self._client.get_or_create_collection(name=name)

    async def add_documents(
        self, documents: List[VectorDocument], collection: Optional[str] = None
    ) -> None:
        if not documents:
            return

        coll = self._get_collection(collection)

        # Calcule les embeddings manquants
        texts_to_embed = [doc.text for doc in documents if doc.embedding is None]
        if texts_to_embed:
            new_embeddings = await self._embedding_provider.embed_batch(texts_to_embed)
            embed_iter = iter(new_embeddings)
            for doc in documents:
                if doc.embedding is None:
                    doc.embedding = next(embed_iter)

        coll.upsert(
            ids=[doc.id for doc in documents],
            embeddings=[doc.embedding for doc in documents],
            documents=[doc.text for doc in documents],
            metadatas=[doc.metadata or {} for doc in documents],
        )

    async def similarity_search(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        coll = self._get_collection(collection)
        query_embedding = await self._embedding_provider.embed_text(query)

        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters or None,
        )

        search_results: List[VectorSearchResult] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_id, doc_text, metadata, distance in zip(ids, documents, metadatas, distances):
            # Chroma retourne une distance L2 ; on la convertit en score de similarite cosinus normalisee
            # Plus la distance est grande, plus bas le score (inverse la distance pour obtenir un score 0-1)
            if distance is not None:
                # Normalise la distance L2 : 1 / (1 + distance) donne un score entre 0 et 1
                score = 1.0 / (1.0 + distance)
            else:
                score = 0.0
            search_results.append(
                VectorSearchResult(
                    id=doc_id,
                    text=doc_text,
                    score=score,
                    metadata=metadata or {},
                )
            )

        return search_results

    async def delete_documents(self, ids: List[str], collection: Optional[str] = None) -> None:
        if not ids:
            return
        coll = self._get_collection(collection)
        coll.delete(ids=ids)

    async def delete_collection(self, collection: Optional[str] = None) -> None:
        name = collection or self._default_collection
        self._client.delete_collection(name=name)
