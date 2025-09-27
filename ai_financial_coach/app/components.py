from __future__ import annotations

import streamlit as st
import plotly.express as px
from ai_financial_coach.core.schemas import BudgetAnalysis


def display_budget_analysis(budget: BudgetAnalysis) -> None:
    """Render the budget insight cards and pie chart."""

    st.subheader("Analisis de Presupuesto")
    income = budget.monthly_income or 0
    expenses = budget.total_expenses or 0
    surplus = income - expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Totales", f"${income:,.2f}")
    col2.metric("Gastos Totales", f"${expenses:,.2f}")
    col3.metric("Balance", f"${surplus:,.2f}", delta=f"{surplus:,.2f}")

    if budget.spending_categories:
        st.subheader("Desglose de Gastos")
        labels = [item.category for item in budget.spending_categories]
        values = [item.amount for item in budget.spending_categories]
        fig = px.pie(values=values, names=labels, title="Gastos de la Sesion")
        st.plotly_chart(fig, use_container_width=True)
