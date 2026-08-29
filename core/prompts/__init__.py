"""
Sous-package prompts : templates de system prompts utilises par chaque agent.

Chaque module expose une (ou plusieurs) fonction(s) qui construisent le
system prompt final a partir de parametres contextuels.
"""

from core.prompts.chat import get_chat_system_prompt
from core.prompts.email import get_email_system_prompt
from core.prompts.incident import get_incident_system_prompt
from core.prompts.meeting import get_meeting_system_prompt
from core.prompts.summary import get_summary_system_prompt

__all__ = [
    "get_chat_system_prompt",
    "get_email_system_prompt",
    "get_incident_system_prompt",
    "get_meeting_system_prompt",
    "get_summary_system_prompt",
]
