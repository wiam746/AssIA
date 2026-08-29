"""Tests du LLMService — interaction avec Ollama."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLLMService:
    """Tests du service LLM (Ollama) : génération de texte et gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_ask_returns_content(self):
        """LLMService.ask doit retourner une réponse avec contenu."""
        from core.llm.service import LLMService

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Voici la réponse générée par le LLM."
        mock_provider.complete = AsyncMock(return_value=mock_response)

        service = LLMService(provider=mock_provider)

        result = await service.ask("Qu'est-ce que RAG ?", system_prompt="Tu es un assistant.")

        assert result.content == "Voici la réponse générée par le LLM."

    @pytest.mark.asyncio
    async def test_ask_with_history(self):
        """LLMService.ask doit inclure l'historique dans la requête au LLM."""
        from core.llm.service import LLMService

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Réponse avec contexte historique."
        mock_provider.complete = AsyncMock(return_value=mock_response)

        service = LLMService(provider=mock_provider)
        history = [
            {"role": "user", "content": "Question précédente ?"},
            {"role": "assistant", "content": "Réponse précédente."},
        ]

        result = await service.ask("Nouvelle question", history=history)

        assert result.content == "Réponse avec contexte historique."
        mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_handles_ollama_error(self):
        """LLMService.ask doit lever une exception si Ollama est indisponible."""
        from core.llm.service import LLMService

        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(side_effect=ConnectionError("Ollama non disponible"))

        service = LLMService(provider=mock_provider)

        with pytest.raises(Exception):
            await service.ask("Question test")
