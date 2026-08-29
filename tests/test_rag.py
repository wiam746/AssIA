"""Tests du RagService — indexation et retrieval de documents."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRagService:
    """Tests du pipeline RAG : indexation et récupération de contexte."""

    @pytest.mark.asyncio
    async def test_index_document_returns_chunk_count(self):
        """index_document doit retourner le nombre de chunks indexés."""
        from services.rag_service import RagService

        mock_vector_store = MagicMock()
        mock_vector_store.add_documents = AsyncMock()

        mock_processor = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.chunk_id = "doc1_chunk_0"
        mock_chunk.text = "Contenu du chunk de test."
        mock_chunk.metadata = {"document_id": "doc1"}
        mock_processor.process.return_value = [mock_chunk, mock_chunk]

        rag = RagService(vector_store=mock_vector_store, document_processor=mock_processor)

        count = await rag.index_document("fake/path.txt", document_id="doc1")

        assert count == 2
        mock_vector_store.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_document_empty_returns_zero(self):
        """index_document retourne 0 si aucun chunk n'est généré (fichier vide)."""
        from services.rag_service import RagService

        mock_vector_store = MagicMock()
        mock_processor = MagicMock()
        mock_processor.process.return_value = []

        rag = RagService(vector_store=mock_vector_store, document_processor=mock_processor)

        count = await rag.index_document("fake/empty.txt", document_id="doc-empty")

        assert count == 0
        mock_vector_store.add_documents.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_context_as_text_format(self):
        """retrieve_context_as_text formatte les résultats avec [Source: ...] prefixe."""
        from services.rag_service import RagService
        from core.vector_store.base import VectorSearchResult

        mock_vector_store = MagicMock()
        mock_result = VectorSearchResult(
            id="chunk_0",
            text="Décision : reporter la démo au 25 janvier.",
            metadata={"document_id": "reunion_jan"},
            score=0.92,
        )
        mock_vector_store.similarity_search = AsyncMock(return_value=[mock_result])

        rag = RagService(vector_store=mock_vector_store)

        texts = await rag.retrieve_context_as_text("décisions réunion janvier")

        assert len(texts) == 1
        assert "[Source: reunion_jan]" in texts[0]
        assert "Décision" in texts[0]

    @pytest.mark.asyncio
    async def test_retrieve_context_filters_by_min_score(self):
        """retrieve_context exclut les résultats dont le score est inférieur au seuil."""
        from services.rag_service import RagService
        from core.vector_store.base import VectorSearchResult

        mock_vector_store = MagicMock()
        good_result = VectorSearchResult(id="c1", text="Bon", metadata={}, score=0.8)
        bad_result = VectorSearchResult(id="c2", text="Mauvais", metadata={}, score=0.2)
        mock_vector_store.similarity_search = AsyncMock(return_value=[good_result, bad_result])

        rag = RagService(vector_store=mock_vector_store)

        results = await rag.retrieve_context("query", min_score=0.5)

        assert len(results) == 1
        assert results[0].id == "c1"
