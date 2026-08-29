"""Agent specialise dans le traitement des comptes-rendus de reunion."""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from core.llm.service import LLMService
from core.prompts.meeting import get_meeting_system_prompt

logger = logging.getLogger("agents.meeting_agent")

_MEETING_ANALYSIS_INSTRUCTION = """Analyse les notes de réunion suivantes et rédige le procès-verbal selon les instructions du system prompt.

Rends ta réponse EXACTEMENT selon cette structure (en conservant ces titres d'en-têtes) :

### Objet
<objet principal de la réunion ou "Non précisé">

### Points abordés
<synthèse détaillée des points discutés>

### Décisions prises
<liste des décisions arrêtées>

### Actions à réaliser
<liste des actions avec responsables et échéances>

### Prochaine réunion
<date/détails de la prochaine réunion ou "Non précisé">

Notes de réunion à traiter :
---
{content}
---
"""


@dataclass
class MeetingAnalysis:
    """Resultat structure de la redaction du proces-verbal de reunion."""

    objet: str
    summary: str
    decisions: str
    actions: str
    prochaine_reunion: str


class MeetingAgent:
    """Agent spécialisé dans la rédaction de procès-verbaux de réunions professionnelles."""

    def __init__(self, llm_service: Optional[LLMService] = None) -> None:
        self.llm_service = llm_service or LLMService()

    @staticmethod
    def _parse_sections(raw_response: str) -> MeetingAnalysis:
        """Parse la reponse structuree du LLM en ses différentes sections."""

        def extract(primary: str, aliases: list[str], next_sections: list[str]) -> str:
            all_names = [primary] + aliases
            pattern = rf"###\s*(?:{'|'.join(all_names)})\s*(.*?)(?:###\s*(?:{'|'.join(next_sections)})|\Z)"
            match = re.search(pattern, raw_response, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        all_headers = [
            "Objet", "Points abordés", "Points abordes", "Resume", "Résumé",
            "Décisions prises", "Decisions prises", "Decisions", "Décisions",
            "Actions à réaliser", "Actions a realiser", "Actions",
            "Prochaine réunion", "Prochaine reunion"
        ]

        objet = extract("Objet", [], all_headers[1:])
        summary = extract("Points abordés", ["Points abordes", "Resume", "Résumé"], all_headers[5:])
        decisions = extract("Décisions prises", ["Decisions prises", "Decisions", "Décisions"], all_headers[9:])
        actions = extract("Actions à réaliser", ["Actions a realiser", "Actions"], all_headers[13:])
        prochaine = extract("Prochaine réunion", ["Prochaine reunion"], [])

        return MeetingAnalysis(
            objet=objet or "Non précisé",
            summary=summary or raw_response.strip(),
            decisions=decisions or "Aucune décision enregistrée",
            actions=actions or "Aucune action à réaliser",
            prochaine_reunion=prochaine or "Non précisé",
        )

    async def process_meeting(
        self,
        *,
        title: str,
        raw_content: str,
        participants: Optional[str] = None,
    ) -> MeetingAnalysis:
        """Analyse un compte-rendu brut et rédigé le procès-verbal structuré."""
        system_prompt = get_meeting_system_prompt(meeting_title=title, participants=participants)
        prompt = _MEETING_ANALYSIS_INSTRUCTION.format(content=raw_content)

        response = await self.llm_service.ask(prompt, system_prompt=system_prompt)

        analysis = self._parse_sections(response.content)
        logger.info("Procès-verbal pour la réunion '%s' rédigé avec succès.", title)
        return analysis
