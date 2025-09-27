import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import json
import logging
from pydantic import BaseModel, Field
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models (unchanged) ---
class SpendingCategory(BaseModel):
    category: str = Field(..., description="Expense category name")
    amount: float = Field(..., description="Amount spent in this category")

class BudgetAnalysis(BaseModel):
    total_expenses: float = Field(..., description="Total monthly expenses")
    monthly_income: Optional[float] = Field(None, description="Monthly income")
    spending_categories: List[SpendingCategory] = Field(..., description="Breakdown of spending by category")

class Debt(BaseModel):
    name: str = Field(..., description="Name of debt")
    amount: float = Field(..., description="Current balance")
    interest_rate: float = Field(..., description="Annual interest rate (%)")
    min_payment: Optional[float] = Field(None, description="Minimum monthly payment")

# --- Database Functions ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS movements
        (id INTEGER PRIMARY KEY, timestamp TEXT, type TEXT, category TEXT, amount REAL, comment TEXT)
    ''')
    conn.commit()
    conn.close()

def save_movements_to_db(movements: List[Dict[str, Any]]):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    for movement in movements:
        c.execute("INSERT INTO movements (timestamp, type, category, amount, comment) VALUES (?, ?, ?, ?, ?)",
                  (movement.get('timestamp'), movement.get('type'), movement.get('category'), movement.get('amount'), movement.get('comment')))
    conn.commit()
    conn.close()

def fetch_data_from_db(start_date, end_date=None):
    conn = sqlite3.connect('database.db')
    
    # Use start_date for both start and end of the range if end_date is not provided
    if end_date is None:
        end_date = start_date

    # Convert date objects to string format 'YYYY-MM-DD'
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # The query will select all records from the start of start_str to the end of end_str
    query = f"SELECT * FROM movements WHERE DATE(timestamp) BETWEEN '{start_str}' AND '{end_str}'"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Main App Logic (Simplified for new structure) ---
class FinanceAdvisorSystem:
    def analyze_finances(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simplified analysis for the new data structure
        total_income = financial_data.get("monthly_income", 0)
        expenses = financial_data.get("manual_expenses", {})
        total_expenses = sum(expenses.values())
        
        budget_analysis = {
            "monthly_income": total_income,
            "total_expenses": total_expenses,
            "spending_categories": [{"category": k, "amount": v} for k, v in expenses.items()]
        }
        
        return {"budget_analysis": budget_analysis}

# --- Display Functions ---
def display_analysis(results: Dict[str, Any]):
    budget_analysis = results.get("budget_analysis", {})
    if not budget_analysis: 
        st.warning("No se pudo generar el análisis de presupuesto.")
        return

    st.subheader("Análisis de Presupuesto")
    income = budget_analysis.get("monthly_income", 0)
    expenses = budget_analysis.get("total_expenses", 0)
    surplus = income - expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Totales", f"${income:,.2f}")
    col2.metric("Gastos Totales", f"${expenses:,.2f}")
    col3.metric("Balance", f"${surplus:,.2f}", delta=f"{surplus:,.2f}")

    if budget_analysis.get("spending_categories"):
        st.subheader("Desglose de Gastos")
        fig = px.pie(values=[c["amount"] for c in budget_analysis["spending_categories"]], 
                     names=[c["category"] for c in budget_analysis["spending_categories"]],
                     title="Gastos de la Sesión")
        st.plotly_chart(fig, use_container_width=True)

# --- Main UI ---
def main():
    st.set_page_config(page_title="Asesor Financiero ARS", layout="wide")
    init_db()

    if 'movements' not in st.session_state:
        st.session_state.movements = []

    with st.sidebar:
        st.title("Asesor Financiero")
        st.info("Registra tus ingresos, gastos y deudas para obtener un análisis.")

        st.divider()

        st.subheader("Descargar Movimientos")
        
        # Date range selection
        date_from = st.date_input("Desde")
        date_to = st.date_input("Hasta", value=None)

        # Placeholder for data fetching logic
        # df_filtered = fetch_data_from_db(date_from, date_to) 
        
        # Placeholder for download buttons
        st.download_button(
           label="Descargar como CSV",
           data="placeholder_csv", # Placeholder
           file_name='movimientos.csv',
           mime='text/csv',
           disabled=True # Will be enabled when data is available
        )
        
        st.download_button(
           label="Descargar como JSON",
           data="placeholder_json", # Placeholder
           file_name='movimientos.json',
           mime='application/json',
           disabled=True # Will be enabled when data is available
        )

    st.title("📊 Asesor Financiero - Argentina")
    st.header("Registra tus Movimientos")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.subheader("📈 Ingresos")
            ingreso_cat = st.radio("Tipo de Ingreso", ["Transferencia", "Débito", "Crédito", "Efectivo"], key="ing_cat", horizontal=True)
            ingreso_monto = st.number_input("Monto (ARS)", min_value=0.0, key="ing_monto", format="%.2f")
            ingreso_comentario = st.text_input("Comentario (opcional)", key="ing_com")
            if st.button("Añadir Ingreso"):
                if ingreso_monto > 0:
                    st.session_state.movements.append({"timestamp": datetime.now().isoformat(), "type": "Ingreso", "category": ingreso_cat, "amount": ingreso_monto, "comment": ingreso_comentario})
                    st.success(f"Ingreso añadido.")
                else:
                    st.warning("El monto debe ser mayor a cero.")

    with col2:
        with st.container(border=True):
            st.subheader("📉 Gastos")
            gasto_cat = st.radio("Categoría de Gasto", ["Fijo", "Variable", "Discrecional"], key="gasto_cat", horizontal=True)
            gasto_monto = st.number_input("Monto (ARS)", min_value=0.0, key="gasto_monto", format="%.2f")
            gasto_comentario = st.text_input("Comentario (opcional)", key="gasto_com")
            if st.button("Añadir Gasto"):
                if gasto_monto > 0:
                    st.session_state.movements.append({"timestamp": datetime.now().isoformat(), "type": "Gasto", "category": gasto_cat, "amount": gasto_monto, "comment": gasto_comentario})
                    st.success(f"Gasto añadido.")
                else:
                    st.warning("El monto debe ser mayor a cero.")

    with col3:
        with st.container(border=True):
            st.subheader("💳 Deudas")
            deuda_cat = st.radio("Tipo de Deuda", ["Tarjeta de crédito", "Préstamo", "Emergencia"], key="deuda_cat", horizontal=True)
            deuda_monto = st.number_input("Monto (ARS)", min_value=0.0, key="deuda_monto", format="%.2f")
            deuda_comentario = st.text_input("Comentario (opcional)", key="deuda_com")
            if st.button("Añadir Deuda"):
                if deuda_monto > 0:
                    st.session_state.movements.append({"timestamp": datetime.now().isoformat(), "type": "Deuda", "category": deuda_cat, "amount": deuda_monto, "comment": deuda_comentario})
                    st.success(f"Deuda añadida.")
                else:
                    st.warning("El monto debe ser mayor a cero.")

    st.divider()

    st.subheader("Movimientos Registrados en esta Sesión")
    if st.session_state.movements:
        df = pd.DataFrame(st.session_state.movements)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no has añadido movimientos en esta sesión.")

    st.divider()

    if st.button("Analizar Finanzas", type="primary", use_container_width=True):
        if not st.session_state.movements:
            st.warning("Por favor, añade al menos un movimiento antes de analizar.")
        else:
            total_income = sum(m['amount'] for m in st.session_state.movements if m['type'] == 'Ingreso')
            manual_expenses = {m['comment'] or m['category']: m['amount'] for m in st.session_state.movements if m['type'] == 'Gasto'}
            debts = [{"name": m['comment'] or m['category'], "amount": m['amount'], "interest_rate": 0, "min_payment": 0} for m in st.session_state.movements if m['type'] == 'Deuda']
            
            financial_data = {
                "monthly_income": total_income,
                "manual_expenses": manual_expenses,
                "debts": debts
            }

            with st.spinner("🤖 Analizando finanzas..."):
                try:
                    advisor = FinanceAdvisorSystem()
                    results = advisor.analyze_finances(financial_data)
                    st.session_state.analysis_results = results
                    
                    save_movements_to_db(st.session_state.movements)
                    st.session_state.movements = []
                    
                    st.success("¡Análisis completo! Los movimientos de esta sesión han sido guardados en la base de datos.")
                    display_analysis(results)
                    st.rerun()

                except Exception as e:
                    st.error(f"Ocurrió un error durante el análisis: {e}")

if __name__ == "__main__":
    main()
