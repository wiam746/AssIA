"""Templates de prompts pour l'agent de chat conversationnel (RAG ciblé et questions générales)."""

from typing import List, Optional

BASE_CHAT_PROMPT = """Tu es un assistant virtuel intelligent et précis.

Directives de réponse :
1. **Questions sur un document, un projet ou un incident spécifique** :
   - Lorsque du contexte documentaire spécifique t'est fourni, réponds STRICTEMENT en te basant sur ce contexte.
   - Ne mélange pas les informations d'autres projets ou documents non fournis.
   - Si la réponse n'est pas présente dans les extraits fournis du document, indique clairement que l'information n'est pas présente dans ce document.

2. **Questions générales / théoriques** :
   - Si la question est de portée générale (ex: concepts, explications théoriques) et ne nécessite pas de fichier précis, réponds avec tes connaissances générales.

3. **Style et ton** :
   - Exprime-toi toujours en français, de façon professionnelle, claire et structurée.
"""


def get_chat_system_prompt(
    context_chunks: Optional[List[str]] = None,
    user_name: Optional[str] = None,
    extra_context: Optional[str] = None,
) -> str:
    """
    Construit le system prompt de l'agent de chat en injectant le contexte filtré.
    """
    prompt = BASE_CHAT_PROMPT

    if extra_context:
        prompt += f"\n\nContexte spécifique (Incident/Projet/Document) :\n{extra_context}\n"

    if user_name:
        prompt += f"\nTu t'adresses à {user_name}.\n"

    if context_chunks:
        joined_context = "\n\n---\n\n".join(context_chunks)
        prompt += f"\n\nContexte documentaire restreint extrait du/des document(s) ciblé(s) :\n\n{joined_context}\n"
    else:
        prompt += "\n\n(Aucun extrait documentaire spécifique trouvé dans le périmètre sélectionné).\n"

    return prompt
