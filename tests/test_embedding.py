"""Tests de l'EmbeddingProvider (Ollama)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.embedding.provider import OllamaEmbeddingProvider

@pytest.mark.asyncio
async def test_embed_text_success():
    provider = OllamaEmbeddingProvider(base_url="http://localhost:11434", model="nomic-embed-text")
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"embedding": [0.1, 0.2, 0.3]})
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        embedding = await provider.embed_text("Texte de test")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert kwargs["json"] == {"model": "nomic-embed-text", "prompt": "Texte de test"}

@pytest.mark.asyncio
async def test_embed_batch():
    provider = OllamaEmbeddingProvider(base_url="http://localhost:11434", model="nomic-embed-text")
    
    with patch.object(provider, "embed_text", new_callable=AsyncMock) as mock_embed_text:
        mock_embed_text.side_effect = [[0.1], [0.2]]
        embeddings = await provider.embed_batch(["Texte 1", "Texte 2"])
        
        assert embeddings == [[0.1], [0.2]]
        assert mock_embed_text.call_count == 2
