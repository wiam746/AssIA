"""Tests du Vector Store Provider (ChromaDB)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.vector_store.provider import ChromaVectorStoreProvider
from core.vector_store.base import VectorDocument

@pytest.fixture
def mock_embedding_provider():
    provider = MagicMock()
    provider.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
    provider.embed_text = AsyncMock(return_value=[0.1, 0.2])
    return provider

@pytest.fixture
def mock_chroma_client():
    client = MagicMock()
    collection = MagicMock()
    client.get_or_create_collection.return_value = collection
    return client

@pytest.mark.asyncio
async def test_add_documents(mock_embedding_provider, mock_chroma_client):
    with patch("chromadb.PersistentClient", return_value=mock_chroma_client):
        store = ChromaVectorStoreProvider(
            persist_dir="./fake_dir",
            default_collection="test_coll",
            embedding_provider=mock_embedding_provider
        )
        
        docs = [
            VectorDocument(id="doc1", text="Contenu 1", metadata={"key": "val1"}),
            VectorDocument(id="doc2", text="Contenu 2", metadata={"key": "val2"})
        ]
        
        await store.add_documents(docs)
        
        # Verify chroma upsert was called with expected arguments
        collection = mock_chroma_client.get_or_create_collection("test_coll")
        collection.upsert.assert_called_once()
        args, kwargs = collection.upsert.call_args
        assert kwargs["ids"] == ["doc1", "doc2"]
        assert kwargs["documents"] == ["Contenu 1", "Contenu 2"]
        assert kwargs["metadatas"] == [{"key": "val1"}, {"key": "val2"}]
        mock_embedding_provider.embed_batch.assert_called_once_with(["Contenu 1", "Contenu 2"])

@pytest.mark.asyncio
async def test_similarity_search(mock_embedding_provider, mock_chroma_client):
    with patch("chromadb.PersistentClient", return_value=mock_chroma_client):
        store = ChromaVectorStoreProvider(
            persist_dir="./fake_dir",
            default_collection="test_coll",
            embedding_provider=mock_embedding_provider
        )
        
        collection = mock_chroma_client.get_or_create_collection("test_coll")
        collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Contenu 1"]],
            "metadatas": [[{"key": "val1"}]],
            "distances": [[0.1]]
        }
        
        results = await store.similarity_search("requete", top_k=1)
        
        assert len(results) == 1
        assert results[0].id == "doc1"
        assert results[0].text == "Contenu 1"
        assert results[0].score == pytest.approx(1.0 / (1.0 + 0.1))
        mock_embedding_provider.embed_text.assert_called_once_with("requete")
