from __future__ import annotations

from typing import Dict

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
        alerts = []
        if income > 0:
            for category, amount in expenses.items():
                ratio = amount / income
                if ratio > 0.15:
                    alerts.append(
                        f"Gasto alto en {category}: {ratio*100:.1f}% del ingreso"
                    )
        if surplus < 0:
            alerts.append("Deficit mensual: gastos superan ingresos")

        message_type = MessageType.ALERT if alerts else MessageType.FINDING
        headline = (
            "Excedente positivo" if surplus >= 0 else "Deficit en flujo mensual"
        )
        content = (
            f"Budget -> {headline}. Ingresos {income:.2f} ARS, gastos {total_expenses:.2f} ARS, "
            f"saldo {surplus:.2f} ARS."
        )
        if alerts:
            content += " Alertas: " + "; ".join(alerts)

        data = {
            "monthly_income": income,
            "total_expenses": total_expenses,
            "surplus": surplus,
            "categories": expenses,
            "alerts": alerts,
        }
        message = self.post(content=content, type=message_type, data=data)
        self.state.record_finding(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
