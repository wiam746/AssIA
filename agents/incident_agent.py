"""Agent specialise dans l'analyse et l'aide a la resolution des incidents."""

import logging
from typing import Optional

from core.llm.service import LLMService
from core.prompts.incident import get_incident_system_prompt
from services.rag_service import RagService

logger = logging.getLogger("agents.incident_agent")

_INCIDENT_ANALYSIS_INSTRUCTION = """Analyse l'incident suivant et fournis :
1. Une reformulation synthetique du probleme.
2. Les causes probables (en te basant sur le contexte fourni s'il y en a).
3. Des pistes de resolution ou de contournement concretes.
4. Le niveau de priorite de traitement recommande.

Titre : {title}

Description :
---
{description}
---
"""


class IncidentAgent:
    """Aide a l'analyse d'incidents en s'appuyant sur l'historique d'incidents similaires (RAG)."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        rag_service: Optional[RagService] = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.rag_service = rag_service or RagService()

    async def analyze_incident(
        self,
        *,
        title: str,
        description: str,
        severity_hint: Optional[str] = None,
        top_k: int = 3,
    ) -> str:
        """Analyse un incident et retourne une synthese exploitable, avec pistes de resolution."""
        related_chunks = await self.rag_service.retrieve_context_as_text(
            f"{title} {description}", top_k=top_k
        )
        related_context = "\n\n".join(related_chunks) if related_chunks else None

        system_prompt = get_incident_system_prompt(
            severity_hint=severity_hint,
            related_context=related_context,
        )
        prompt = _INCIDENT_ANALYSIS_INSTRUCTION.format(title=title, description=description)

        response = await self.llm_service.ask(prompt, system_prompt=system_prompt)
        logger.info("Incident '%s' analyse (severite=%s).", title, severity_hint)
        return response.content
