from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai_financial_coach.core.schemas import Message, MessageType
from ai_financial_coach.core.state import SharedState


class BaseAgent(ABC):
    """Common base class for every autonomous agent in the system."""

    name: str = "agent"
    role: str = ""
    description: str = ""

    def __init__(
        self, state: SharedState, *, system_prompt: Optional[str] = None
    ) -> None:
        self.state = state
        self.system_prompt = system_prompt or ""
        self._last_signature: Optional[str] = None

    # -- Interaction helpers -------------------------------------------------
    def post(
        self,
        *,
        content: str,
        type: MessageType,
        to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Message:
        return self.state.post_message(
            sender=self.name, type=type, content=content, to=to, data=data
        )

    def read(self) -> List[Message]:
        return self.state.read_messages(self.name)

    def inject(self, message: Message) -> Message:
        return self.state.inject_message(message)

    # -- Lifecycle ------------------------------------------------------------
    @abstractmethod
    def tick(self) -> Optional[Message]:
        """Process new information and optionally emit a message."""

    def observe(self, event: Message) -> None:
        """Hook for subclasses to react to individual messages if needed."""
        # Default implementation is a no-op.

    def configure(self, **kwargs: Any) -> None:
        """Update runtime configuration such as prompts or thresholds."""
        if "system_prompt" in kwargs and isinstance(kwargs["system_prompt"], str):
            self.system_prompt = kwargs["system_prompt"]

    def reset(self) -> None:
        """Optional cleanup before starting a new round."""
        self._last_signature = None

    # -- Change detection -----------------------------------------------------
    def should_run(self, signature: str) -> bool:
        if signature == self._last_signature:
            return False
        self._last_signature = signature
        return True
