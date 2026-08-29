"""Agent specialise dans la redaction et l'analyse d'emails professionnels."""

import logging
import re
from typing import Optional, Tuple

from core.llm.service import LLMService
from core.prompts.email import get_email_system_prompt

logger = logging.getLogger("agents.email_agent")

_DRAFT_INSTRUCTION = """Redige un email professionnel a partir des instructions suivantes.

Reponds EXACTEMENT sous ce format :

Objet: <objet de l'email>

<corps de l'email>

Instructions :
---
{instructions}
---
{recipient_hint}
"""

_ANALYSIS_INSTRUCTION = """Analyse l'email suivant et fournis :
1. Un resume de la demande.
2. Le niveau d'urgence percu (faible / moyen / eleve).
3. Les actions attendues.
4. Une suggestion de reponse courte, si pertinent.

Email a analyser :
---
{content}
---
"""


class EmailAgent:
    """Redige des emails professionnels ou analyse des emails recus, via le LLM."""

    def __init__(self, llm_service: Optional[LLMService] = None) -> None:
        self.llm_service = llm_service or LLMService()

    @staticmethod
    def _parse_draft(raw_response: str) -> Tuple[Optional[str], str]:
        """Extrait l'objet et le corps d'un email genere au format attendu."""
        match = re.search(r"Objet\s*:\s*(.+)", raw_response, re.IGNORECASE)
        subject = match.group(1).strip() if match else None

        body = re.sub(r"Objet\s*:.*\n?", "", raw_response, count=1, flags=re.IGNORECASE).strip()
        return subject, body or raw_response.strip()

    async def draft_email(
        self,
        *,
        instructions: str,
        tone: str = "neutre",
        recipient_name: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        """Genere un email (objet + corps) a partir d'instructions libres."""
        system_prompt = get_email_system_prompt(mode="redaction", tone=tone)  # type: ignore[arg-type]

        recipient_hint = f"\nDestinataire : {recipient_name}." if recipient_name else ""
        prompt = _DRAFT_INSTRUCTION.format(instructions=instructions, recipient_hint=recipient_hint)

        response = await self.llm_service.ask(prompt, system_prompt=system_prompt)

        subject, body = self._parse_draft(response.content)
        logger.info("Email redige (objet='%s').", subject)
        return subject, body

    async def analyze_email(self, *, email_content: str) -> str:
        """Analyse un email recu et retourne une synthese structuree."""
        system_prompt = get_email_system_prompt(mode="analyse")
        prompt = _ANALYSIS_INSTRUCTION.format(content=email_content)

        response = await self.llm_service.ask(prompt, system_prompt=system_prompt)
        logger.info("Email analyse avec succes.")
        return response.content
