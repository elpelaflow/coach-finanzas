from __future__ import annotations

from typing import Dict, Optional

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class BudgetAgent(BaseAgent):
    name = "budget"
    role = "Budget analyst"

    def tick(self):  # type: ignore[override]
        inputs = self.state.inputs
        income = float(inputs.get("monthly_income", 0) or 0)
        expenses: Dict[str, float] = {
            key: float(value or 0)
            for key, value in (inputs.get("manual_expenses") or {}).items()
        }
        signature = f"{income}|{sorted(expenses.items())}"
        if not self.should_run(signature):
            return None

        total_expenses = sum(expenses.values())
        surplus = income - total_expenses
        message_type = MessageType.FINDING if surplus >= 0 else MessageType.ALERT
        headline = (
            "Excedente positivo" if surplus >= 0 else "Deficit en flujo mensual"
        )
        content = (
            f"Budget -> {headline}. Ingresos {income:.2f} ARS, gastos {total_expenses:.2f} ARS, "
            f"saldo {surplus:.2f} ARS."
        )
        data = {
            "monthly_income": income,
            "total_expenses": total_expenses,
            "surplus": surplus,
            "categories": expenses,
        }
        message = self.post(content=content, type=message_type, data=data)
        self.state.record_finding(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
