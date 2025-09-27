from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from ai_financial_coach.core.schemas import Message, MessageType


@dataclass
class MessageBus:
    log: List[Message] = field(default_factory=list)
    cursors: Dict[str, int] = field(default_factory=dict)

    def post(
        self,
        *,
        message: Optional[Message] = None,
        sender: Optional[str] = None,
        type: Optional[MessageType] = None,
        content: Optional[str] = None,
        to: Optional[str] = None,
        data: Optional[Dict[str, object]] = None,
    ) -> Message:
        if message is None:
            if sender is None or type is None or content is None:
                raise ValueError("sender, type and content are required when message is None")
            message = Message(sender=sender, type=type, content=content, to=to, data=data)
        self.log.append(message)
        return message

    def extend(self, messages: Iterable[Message]) -> None:
        for message in messages:
            self.post(message=message)

    def read_since(self, agent: str, cursor: Optional[int] = None) -> List[Message]:
        start = cursor if cursor is not None else self.cursors.get(agent, 0)
        if start < 0:
            start = 0
        if start > len(self.log):
            start = len(self.log)
        items = self.log[start:]
        self.cursors[agent] = len(self.log)
        return items

    def peek(self, start: int = 0) -> List[Message]:
        if start < 0:
            start = 0
        return self.log[start:]

    def reset(self) -> None:
        self.log.clear()
        self.cursors.clear()

    def cursor_for(self, agent: str) -> int:
        return self.cursors.get(agent, 0)

    def set_cursor(self, agent: str, position: Optional[int] = None) -> None:
        if position is None:
            position = len(self.log)
        self.cursors[agent] = max(0, position)
