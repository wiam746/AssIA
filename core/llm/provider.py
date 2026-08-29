"""Implementation concrete du provider LLM : Ollama (API REST locale)."""

import json
from typing import Any, AsyncIterator, List, Optional

from config.settings import settings
from core.llm.base import BaseLLMProvider, LLMMessage, LLMResponse, LLMRole


class OllamaProvider(BaseLLMProvider):
    """Provider LLM base sur un serveur Ollama local (API REST)."""

    provider_name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    @staticmethod
    def _to_ollama_messages(messages: List[LLMMessage], system_prompt: Optional[str]) -> List[dict]:
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        for m in messages:
            role = "assistant" if m.role == LLMRole.ASSISTANT else m.role.value
            payload.append({"role": role, "content": m.content})
        return payload

    async def complete(
        self,
        messages: List[LLMMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        import httpx

        payload = {
            "model": self.model,
            "messages": self._to_ollama_messages(messages, system_prompt),
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.llm_temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            finish_reason="stop" if data.get("done") else None,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            raw=data,
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        import httpx

        payload = {
            "model": self.model,
            "messages": self._to_ollama_messages(messages, system_prompt),
            "stream": True,
            "options": {
                "temperature": temperature if temperature is not None else settings.llm_temperature,
                "num_predict": max_tokens or settings.llm_max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
