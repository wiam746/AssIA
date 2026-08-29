"""
Service applicatif au-dessus du provider LLM : gestion des prompts,
de l'historique de conversation, des retries et de la journalisation.

Les agents (chat_agent, meeting_agent, ...) consomment ce service plutot
que d'appeler directement un provider.
"""

import logging
from typing import Any, AsyncIterator, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from core.llm.base import BaseLLMProvider, LLMMessage, LLMResponse, LLMRole
from core.llm.factory import get_llm_provider

logger = logging.getLogger("core.llm")


class LLMServiceError(Exception):
    """Erreur levee lorsque le LLM ne parvient pas a repondre malgre les retries."""


class LLMService:
    """
    Point d'entree haut-niveau pour interagir avec un LLM.

    Fournit :
      - la gestion d'historique de conversation,
      - l'injection de system prompt,
      - le retry automatique en cas d'erreur transitoire,
      - le streaming.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        self.provider = provider or get_llm_provider()

    @staticmethod
    def build_history(
        history: Optional[List[dict]] = None,
    ) -> List[LLMMessage]:
        """Convertit un historique brut (liste de dicts) en liste de LLMMessage."""
        messages: List[LLMMessage] = []
        for item in history or []:
            role = LLMRole(item["role"])
            messages.append(LLMMessage(role=role, content=item["content"]))
        return messages

    @retry(
        reraise=True,
        stop=stop_after_attempt(settings.llm_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def _complete_with_retry(
        self,
        messages: List[LLMMessage],
        *,
        temperature: Optional[float],
        max_tokens: Optional[int],
        system_prompt: Optional[str],
        **kwargs: Any,
    ) -> LLMResponse:
        return await self.provider.complete(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def ask(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        history: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Envoie un prompt utilisateur (avec historique optionnel) au LLM
        et retourne la reponse completee, avec retry automatique.
        """
        messages = self.build_history(history)
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        try:
            response = await self._complete_with_retry(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            )
            logger.debug(
                "LLM completion OK (provider=%s, tokens=%s)",
                self.provider.provider_name,
                response.total_tokens,
            )
            return response
        except Exception as exc:
            logger.error("Echec de la completion LLM apres retries : %s", exc)
            raise LLMServiceError(str(exc)) from exc

    async def ask_stream(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        history: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Envoie un prompt et retourne la reponse en streaming (chunks de texte)."""
        messages = self.build_history(history)
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))

        try:
            async for chunk in self.provider.stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            ):
                yield chunk
        except Exception as exc:
            logger.error("Echec du streaming LLM : %s", exc)
            raise LLMServiceError(str(exc)) from exc
