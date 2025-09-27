from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from openai import OpenAI


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")


@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMClient:
    """Thin wrapper around the OpenAI SDK configured for OpenRouter."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url or os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
        self.model = model or DEFAULT_MODEL
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("OPENROUTER_API_KEY is not configured")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [message.to_dict() for message in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)
        response = self.client.chat.completions.create(**payload)
        return response.to_dict()

    def structured_complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_format: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if response_format is not None:
            kwargs.setdefault("extra", {})
            kwargs["extra"]["response_format"] = response_format
        return self.complete(messages, **kwargs)


def build_conversation(
    *, system_prompt: str, user_prompt: str, history: Optional[Iterable[ChatMessage]] = None
) -> List[ChatMessage]:
    conversation: List[ChatMessage] = [ChatMessage(role="system", content=system_prompt)]
    if history:
        conversation.extend(history)
    conversation.append(ChatMessage(role="user", content=user_prompt))
    return conversation
