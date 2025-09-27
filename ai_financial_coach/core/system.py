from __future__ import annotations

from typing import Any, Dict, List

from ai_financial_coach.core.schemas import BudgetAnalysis, SpendingCategory


class FinanceAdvisorSystem:
    """Simplified financial analysis placeholder.

    The implementation will evolve as the multi-agent engine is introduced, but
    for now it keeps the original behaviour so the current UI stays intact.
    """

    def analyze_finances(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        income = float(financial_data.get("monthly_income", 0) or 0)
        expenses_map: Dict[str, float] = {
            key: float(value or 0)
            for key, value in (financial_data.get("manual_expenses") or {}).items()
        }
        total_expenses = sum(expenses_map.values())
        categories: List[SpendingCategory] = [
            SpendingCategory(category=key, amount=value)
            for key, value in expenses_map.items()
        ]

        budget = BudgetAnalysis(
            monthly_income=income,
            total_expenses=total_expenses,
            spending_categories=categories,
        )

        return {"budget_analysis": budget}
