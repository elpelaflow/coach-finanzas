from __future__ import annotations

from typing import List

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class DebtAgent(BaseAgent):
    name = "debt"
    role = "Debt optimizer"

    def tick(self):  # type: ignore[override]
        debts: List[dict] = self.state.inputs.get("debts", [])  # type: ignore[assignment]
        if not debts:
            return None

        budget = self.state.findings.get("budget") or {}
        surplus = float(budget.get("surplus", 0))
        alerts = budget.get("alerts", [])
        signature = f"{surplus}|{len(debts)}|{sum(d.get('amount', 0) for d in debts)}|{alerts}"
        if not self.should_run(signature):
            return None

        total_debt = sum(float(item.get("amount", 0)) for item in debts)
        avalanche = 0.0
        snowball = 0.0
        if surplus <= 0:
            content = (
                "Debt -> Sin excedente disponible. Recomiendo priorizar minimo de deudas y negociar tasas."
            )
            message_type = MessageType.ALERT
        else:
            avalanche_ratio = 0.6 if not alerts else 0.55
            snowball_ratio = 0.4 if not alerts else 0.45
            avalanche = max(0.0, round(surplus * avalanche_ratio, 2))
            snowball = max(0.0, round(surplus * snowball_ratio, 2))
            suffix = " y monitorear categorias criticas." if alerts else ""
            content = (
                "Debt -> Plan propuesto: asignar "
                f"{int(avalanche_ratio*100)}% del excedente a avalanche y "
                f"{int(snowball_ratio*100)}% a snowball" + suffix
            )
            message_type = MessageType.PROPOSAL
        data = {
            "surplus": surplus,
            "total_debt": total_debt,
            "avalanche_payment": avalanche,
            "snowball_payment": snowball,
            "alerts": alerts,
        }
        message = self.post(content=content, type=message_type, data=data)
        self.state.record_plan(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
