from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_financial_coach.core.message_bus import MessageBus
from ai_financial_coach.core.schemas import GoalsState, Message, MessageType


@dataclass
class SharedState:
    inputs: Dict[str, Any] = field(default_factory=dict)
    goals: GoalsState = field(default_factory=GoalsState)
    findings: Dict[str, Any] = field(default_factory=dict)
    plans: Dict[str, Any] = field(default_factory=dict)
    llm_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    message_bus: MessageBus = field(default_factory=MessageBus)

    def update_inputs(self, **kwargs: Any) -> None:
        self.inputs.update(kwargs)

    def set_goals(self, goals: GoalsState) -> None:
        self.goals = goals

    def record_finding(self, agent: str, payload: Any) -> None:
        self.findings[agent] = payload

    def record_plan(self, agent: str, payload: Any) -> None:
        self.plans[agent] = payload

    def update_llm_status(self, agent: str, **kwargs: Any) -> None:
        bucket = self.llm_status.setdefault(agent, {})
        bucket.update(kwargs)

    def post_message(
        self,
        *,
        sender: str,
        type: MessageType,
        content: str,
        to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Message:
        return self.message_bus.post(
            sender=sender, type=type, content=content, to=to, data=data
        )

    def inject_message(self, message: Message) -> Message:
        return self.message_bus.post(message=message)

    def read_messages(self, agent: str) -> List[Message]:
        return self.message_bus.read_since(agent)

    @property
    def log(self) -> List[Message]:
        return self.message_bus.log

    def reset(self) -> None:
        self.inputs.clear()
        self.findings.clear()
        self.plans.clear()
        self.llm_status.clear()
        self.message_bus.reset()
