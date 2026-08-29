"""
Interface abstraite pour les providers LLM.

Tout provider concret (OpenAI, Anthropic, ...) doit implementer
`BaseLLMProvider` afin de rester interchangeable via la factory,
sans que le reste de l'application ne dependent d'un SDK particulier.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional


class LLMRole(str, Enum):
    """Roles possibles dans un historique de conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Un message unique dans un historique de conversation, independant du provider."""

    role: LLMRole
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class LLMResponse:
    """Reponse normalisee retournee par un provider LLM, quel qu'il soit."""

    content: str
    model: str
    finish_reason: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    raw: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseLLMProvider(ABC):
    """
    Interface que tout provider LLM concret doit respecter.

    Cette abstraction permet de changer de fournisseur (OpenAI, Anthropic, ...)
    via la simple variable d'environnement LLM_PROVIDER, sans impacter les
    agents ou services qui consomment le LLM.
    """

    provider_name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Genere une reponse completee a partir d'un historique de messages."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Genere une reponse en streaming, token par token / chunk par chunk."""
        raise NotImplementedError
        yield ""  # pragma: no cover - permet a mypy de reconnaitre le type generateur

    async def health_check(self) -> bool:
        """Verifie que le provider est correctement configure et joignable."""
        try:
            await self.complete(
                [LLMMessage(role=LLMRole.USER, content="ping")],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
