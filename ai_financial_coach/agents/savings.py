from __future__ import annotations

from typing import List

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class SavingsAgent(BaseAgent):
    name = "savings"
    role = "Savings strategy"

    def tick(self):  # type: ignore[override]
        budget = self.state.findings.get("budget")
        if not budget:
            return None
        surplus = float(
            budget.get("surplus", budget.get("monthly_income", 0) - budget.get("total_expenses", 0))
        )
        alerts: List[str] = budget.get("alerts", [])
        signature = f"{surplus}|{budget.get('total_expenses')}|{alerts}"
        if not self.should_run(signature):
            return None

        if surplus <= 0:
            content = "Savings -> Sin excedente para asignar. Solicitar ajustes al presupuesto."
            message = self.post(content=content, type=MessageType.ALERT, data={"surplus": surplus})
            self.state.record_plan(self.name, {"status": "blocked", "surplus": surplus})
            return message

        emergency_ratio = 0.5
        automation_ratio = 0.3
        discretionary_ratio = 0.2
        if alerts:
            emergency_ratio = 0.6
            automation_ratio = 0.25
            discretionary_ratio = 0.15

        emergency = round(surplus * emergency_ratio, 2)
        automation = round(surplus * automation_ratio, 2)
        discretionary = round(surplus - emergency - automation, 2)
        data = {
            "surplus": surplus,
            "emergency_allocation": emergency,
            "automation_allocation": automation,
            "discretionary_allocation": discretionary,
            "alerts": alerts,
        }
        suffix = " Ajustar gastos identificados antes de ampliar metas flexibles." if alerts else ""
        content = (
            "Savings -> Propuesta de asignacion: "
            f"{int(emergency_ratio*100)}% fondo emergencia, {int(automation_ratio*100)}% automatizaciones, "
            f"{int(discretionary_ratio*100)}% metas flexibles." + suffix
        )
        message = self.post(content=content, type=MessageType.PROPOSAL, data=data)
        self.state.record_plan(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
