"""Agent specialise dans l'assistance a la gestion de projet."""

import logging
from typing import Optional

from core.llm.service import LLMService

logger = logging.getLogger("agents.project_agent")

_PROJECT_SYSTEM_PROMPT = """Tu es un assistant specialise en gestion de projet.

Ta mission :
- Proposer des prochaines etapes concretes et priorisees pour un projet donne.
- Tenir compte du statut actuel du projet (actif, en pause, termine, archive).
- Rester pragmatique et actionnable, sans generer de plan generique hors-sujet.
- Reponds en francais, sous forme de liste a puces courte (3 a 6 items).
"""

_NEXT_STEPS_INSTRUCTION = """Projet : {name}
Statut actuel : {status}

Description :
---
{description}
---

Propose les prochaines etapes recommandees pour ce projet.
"""


class ProjectAgent:
    """Fournit une assistance a la gestion de projet (suggestions de prochaines etapes)."""

    def __init__(self, llm_service: Optional[LLMService] = None) -> None:
        self.llm_service = llm_service or LLMService()

    async def suggest_next_steps(
        self,
        *,
        name: str,
        description: str,
        status: str,
    ) -> str:
        """Suggere les prochaines etapes pertinentes pour un projet donne."""
        prompt = _NEXT_STEPS_INSTRUCTION.format(name=name, description=description, status=status)

        response = await self.llm_service.ask(prompt, system_prompt=_PROJECT_SYSTEM_PROMPT)
        logger.info("Suggestions generees pour le projet '%s'.", name)
        return response.content
