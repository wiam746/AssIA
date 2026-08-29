"""Implementation concrete du provider d'embeddings : Ollama (API REST locale)."""

from typing import List, Optional

from config.settings import settings
from core.embedding.base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Provider d'embeddings base sur un serveur Ollama local (API REST)."""

    provider_name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed_text(self, text: str) -> List[float]:
        import httpx

        payload = {"model": self.model, "prompt": text}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get("embedding", [])

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]