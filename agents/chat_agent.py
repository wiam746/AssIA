"""Agent de chat conversationnel, s'appuyant sur le RAG filtré par document/projet pour repondre aux questions."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from core.llm.service import LLMService
from core.prompts.chat import get_chat_system_prompt
from services.rag_service import RagService

logger = logging.getLogger("agents.chat_agent")


@dataclass
class ChatAnswer:
    """Reponse structuree de l'agent de chat."""

    content: str
    sources: List[str] = field(default_factory=list)


class ChatAgent:
    """
    Agent conversationnel principal : recupere du contexte pertinent via le RAG,
    en filtrant optionnellement par document ou liste de documents,
    puis interroge le LLM pour produire une reponse sourcee.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        rag_service: Optional[RagService] = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.rag_service = rag_service or RagService()

    async def answer(
        self,
        question: str,
        *,
        history: Optional[List[dict]] = None,
        user_name: Optional[str] = None,
        extra_context: Optional[str] = None,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> ChatAnswer:
        """Repond a une question utilisateur en filtrant le contexte documentaire si un document est specifie."""
        filters = None
        if document_id:
            filters = {"document_id": document_id}
        elif document_ids:
            if len(document_ids) == 1:
                filters = {"document_id": document_ids[0]}
            elif len(document_ids) > 1:
                filters = {"document_id": {"$in": document_ids}}

        context_chunks = await self.rag_service.retrieve_context_as_text(
            question, top_k=top_k, filters=filters
        )

        system_prompt = get_chat_system_prompt(
            context_chunks=context_chunks,
            user_name=user_name,
            extra_context=extra_context,
        )

        response = await self.llm_service.ask(
            question,
            system_prompt=system_prompt,
            history=history,
        )

        logger.debug("Reponse generee (sources=%d, filter=%s).", len(context_chunks), filters)

        return ChatAnswer(content=response.content, sources=context_chunks)
