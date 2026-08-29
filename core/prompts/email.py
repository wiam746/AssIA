"""Templates de prompts pour l'agent de redaction / analyse d'emails."""

from typing import Literal, Optional

EmailTone = Literal["formel", "neutre", "cordial"]

_TONE_INSTRUCTIONS = {
    "formel": "Adopte un ton formel et institutionnel, vouvoiement systematique.",
    "neutre": "Adopte un ton professionnel neutre, clair et factuel.",
    "cordial": "Adopte un ton professionnel mais chaleureux et accessible.",
}

BASE_EMAIL_DRAFTING_PROMPT = """Tu es un assistant specialise dans la redaction d'emails professionnels.

Regles :
- Redige des emails clairs, bien structures (objet, salutation, corps, formule de politesse).
- Reste fidele aux informations et instructions fournies par l'utilisateur.
- N'invente jamais de faits, de dates ou d'engagements non mentionnes.
- Reponds en francais, sauf demande explicite contraire.
"""

BASE_EMAIL_ANALYSIS_PROMPT = """Tu es un assistant specialise dans l'analyse d'emails professionnels.

Ta mission :
- Extraire les informations cles (expediteur, sujet, demandes, echeances, actions attendues).
- Identifier le niveau d'urgence et le ton du message.
- Proposer, si pertinent, une reponse adaptee ou une action de suivi.
- Reponds en francais, de maniere structuree.
"""


def get_email_system_prompt(
    mode: Literal["redaction", "analyse"] = "redaction",
    tone: Optional[EmailTone] = "neutre",
) -> str:
    """
    Construit le system prompt pour l'agent email.

    Args:
        mode: "redaction" pour generer un email, "analyse" pour en extraire des informations.
        tone: ton souhaite pour la redaction (ignore en mode "analyse").
    """
    if mode == "analyse":
        return BASE_EMAIL_ANALYSIS_PROMPT

    prompt = BASE_EMAIL_DRAFTING_PROMPT
    if tone:
        prompt += f"\n{_TONE_INSTRUCTIONS.get(tone, _TONE_INSTRUCTIONS['neutre'])}\n"

    return prompt
