"""Templates de prompts pour l'agent de gestion des incidents."""

from typing import Optional

BASE_INCIDENT_PROMPT = """Tu es un assistant specialise dans la gestion et l'analyse d'incidents \
techniques ou operationnels au sein de l'entreprise.

Ta mission :
- Aider a structurer la description d'un incident (contexte, impact, gravite, cause probable).
- Proposer des pistes de resolution ou de contournement realistes.
- Identifier si des incidents similaires ont deja ete rencontres (a partir du contexte fourni).
- Rester factuel : ne jamais affirmer une cause sans indice suffisant dans le contexte.
- Reponds en francais, de maniere structuree et actionnable.
"""


def get_incident_system_prompt(
    severity_hint: Optional[str] = None,
    related_context: Optional[str] = None,
) -> str:
    """
    Construit le system prompt pour l'agent incident.

    Args:
        severity_hint: indication de gravite deja connue (ex: "critique", "mineur").
        related_context: extraits d'incidents similaires issus du RAG.
    """
    prompt = BASE_INCIDENT_PROMPT

    if severity_hint:
        prompt += f"\nGravite indicative de l'incident en cours : {severity_hint}.\n"

    if related_context:
        prompt += f"\n\nIncidents similaires trouves dans l'historique :\n\n{related_context}\n"

    return prompt
