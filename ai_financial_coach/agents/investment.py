from __future__ import annotations

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.schemas import MessageType


class InvestmentAgent(BaseAgent):
    name = "investment"
    role = "Investment scenarios"

    def tick(self):  # type: ignore[override]
        budget = self.state.findings.get("budget") or {}
        plans = self.state.plans
        surplus = float(budget.get("surplus", 0))
        savings_plan = plans.get("savings", {})
        debts_plan = plans.get("debt", {})
        signature = f"{surplus}|{bool(savings_plan)}|{bool(debts_plan)}"
        if surplus <= 0 or not self.should_run(signature):
            return None

        if debts_plan and debts_plan.get("total_debt", 0) > 0 and surplus < 1000:
            content = "Investment -> Priorizar cancelacion de deudas antes de invertir."
            return self.post(content=content, type=MessageType.INFO)

        conservative = round(surplus * 0.2, 2)
        balanced = round(surplus * 0.5, 2)
        accelerated = round(surplus * 0.8, 2)
        data = {
            "surplus": surplus,
            "conservative": conservative,
            "balanced": balanced,
            "accelerated": accelerated,
        }
        content = (
            "Investment -> Escenarios sugeridos para excedente actual (20% conservador, "
            "50% balanceado, 80% acelerado)."
        )
        message = self.post(content=content, type=MessageType.PROPOSAL, data=data)
        self.state.record_plan(self.name, data)
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
