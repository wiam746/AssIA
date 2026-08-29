"""Templates de prompts pour la generation de resumes (documents, reunions, threads...)."""

from typing import Literal, Optional

SummaryLength = Literal["court", "moyen", "detaille"]

_LENGTH_INSTRUCTIONS = {
    "court": "Produis un resume en 3 a 5 puces maximum, tres synthetique.",
    "moyen": "Produis un resume structure en 1 a 2 paragraphes, avec les points cles.",
    "detaille": "Produis un resume detaille et structure, avec sections si pertinent.",
}

BASE_SUMMARY_PROMPT = """Tu es un assistant specialise dans la synthese de documents professionnels.

Ta mission :
- Identifier les informations essentielles du texte fourni.
- Restituer ces informations de maniere fidele, sans invention ni interpretation abusive.
- Structurer le resume pour qu'il soit directement exploitable par un lecteur presse.
- Repondre en francais.
"""


def get_summary_system_prompt(
    length: SummaryLength = "moyen",
    focus: Optional[str] = None,
) -> str:
    """
    Construit le system prompt pour la generation d'un resume.

    Args:
        length: niveau de detail souhaite ("court", "moyen", "detaille").
        focus: axe particulier sur lequel le resume doit insister
            (ex: "decisions prises", "risques identifies").
    """
    prompt = BASE_SUMMARY_PROMPT
    prompt += f"\n{_LENGTH_INSTRUCTIONS.get(length, _LENGTH_INSTRUCTIONS['moyen'])}\n"

    if focus:
        prompt += f"\nMets particulierement l'accent sur : {focus}.\n"

    return prompt
