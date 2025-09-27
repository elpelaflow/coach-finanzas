from __future__ import annotations

from typing import List, Optional

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import GoalsState, MessageType


class ManagerAgent(BaseAgent):
    name = "manager"
    role = "Conversational manager"

    def __init__(
        self,
        state,
        *,
        system_prompt: Optional[str] = None,
        goals: Optional[GoalsState] = None,
    ) -> None:
        super().__init__(state, system_prompt=system_prompt)
        self.goals = goals or GoalsState()
        self._history: List[str] = []
        self._last_brief_count: int = 0

    def handle_user_message(self, content: str) -> None:
        self._history.append(content)
        headline = content[:60]
        self.state.post_message(
            sender="user",
            type=MessageType.INFO,
            content=f"Usuario -> Manager: {headline}",
            data={"full_text": content},
        )
        self.post(
            content="Manager -> Usuario: Recibido, coordinare con el equipo.",
            type=MessageType.INFO,
        )

    def update_goals(self, goals: GoalsState) -> None:
        self.goals = goals
        self.state.set_goals(goals)
        self.post(
            content="Manager actualizo objetivos compartidos.",
            type=MessageType.DECISION,
            data=goals.dict(),
        )
        self.state.record_plan(
            "manager",
            {
                "goals": goals.dict(),
                "delegations": [],
            },
        )

    def tick(self):  # type: ignore[override]
        findings_count = len(self.state.findings)
        if findings_count == 0 or findings_count == self._last_brief_count:
            return None

        summary = "+ ".join(sorted(self.state.findings.keys()))
        content = (
            "Manager: resumen de hallazgos disponibles -> "
            f"{summary if summary else 'sin hallazgos'}"
        )
        message = self.post(
            content=content,
            type=MessageType.INFO,
            data={"findings_count": findings_count},
        )
        self._last_brief_count = findings_count
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
        self._history.clear()
        self._last_brief_count = 0
