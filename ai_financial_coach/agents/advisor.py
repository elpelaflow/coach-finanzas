from __future__ import annotations

from typing import Dict, List

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class AdvisorAgent(BaseAgent):
    name = "advisor"
    role = "Human facing advisor"

    def tick(self):  # type: ignore[override]
        plans = self.state.plans
        findings = self.state.findings
        signature = f"{sorted(plans.keys())}|{sorted(findings.keys())}"
        if not plans and not findings:
            return None
        if not self.should_run(signature):
            return None

        steps: List[str] = []
        budget = findings.get("budget")
        if budget:
            surplus = budget.get("surplus", 0)
            steps.append(f"Revisar excedente mensual estimado: {surplus:.2f} ARS")
        savings = plans.get("savings")
        if savings:
            steps.append(
                "Asignar excedente: 50% fondo emergencia, 30% automatizaciones, 20% metas flexibles"
            )
        debt = plans.get("debt")
        if debt and debt.get("avalanche_payment", 0) > 0:
            steps.append(
                "Aplicar 60% del excedente a avalanche y 40% a snowball para reducir intereses"
            )
        investments = plans.get("investment")
        if investments:
            steps.append("Evaluar escenarios de inversion antes de los proximos 90 dias")

        content = "Advisor -> Plan resumido: " + " | ".join(steps)
        data: Dict[str, object] = {
            "steps": steps,
            "goals": self.state.goals.dict(),
        }
        message = self.post(content=content, type=MessageType.INFO, data=data)
        self.state.record_plan(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
