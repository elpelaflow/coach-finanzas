from __future__ import annotations

from typing import Optional

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class SavingsAgent(BaseAgent):
    name = "savings"
    role = "Savings strategy"

    def tick(self):  # type: ignore[override]
        budget = self.state.findings.get("budget")
        if not budget:
            return None
        surplus = float(budget.get("surplus", budget.get("monthly_income", 0) - budget.get("total_expenses", 0)))
        signature = f"{surplus}|{budget.get('total_expenses')}"
        if not self.should_run(signature):
            return None

        if surplus <= 0:
            content = "Savings -> Sin excedente para asignar. Solicitar ajustes al presupuesto."
            message = self.post(content=content, type=MessageType.ALERT, data={"surplus": surplus})
            self.state.record_plan(self.name, {"status": "blocked", "surplus": surplus})
            return message

        emergency = round(surplus * 0.5, 2)
        automation = round(surplus * 0.3, 2)
        discretionary = round(surplus - emergency - automation, 2)
        data = {
            "surplus": surplus,
            "emergency_allocation": emergency,
            "automation_allocation": automation,
            "discretionary_allocation": discretionary,
        }
        content = (
            "Savings -> Propuesta de asignacion: 50% fondo emergencia, 30% automatizaciones, "
            "20% metas flexibles."
        )
        message = self.post(content=content, type=MessageType.PROPOSAL, data=data)
        self.state.record_plan(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
