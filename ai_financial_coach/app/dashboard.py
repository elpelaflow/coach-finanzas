from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from ai_financial_coach.agents import AgentTeam
from ai_financial_coach.app.components import display_budget_analysis
from ai_financial_coach.app.context import get_agent_team, get_shared_state
from ai_financial_coach.core.database import save_movements_to_db
from ai_financial_coach.core.schemas import BudgetAnalysis, MessageType
from ai_financial_coach.core.state import SharedState
from ai_financial_coach.core.system import FinanceAdvisorSystem


def ensure_session_state() -> None:
    st.session_state.setdefault("movements", [])
    st.session_state.setdefault("analysis_results", None)
    st.session_state.setdefault("last_round_outputs", {})


def add_movement(entry: Dict[str, Any]) -> None:
    st.session_state.movements.append(entry)


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Asesor Financiero")
        st.info("Registra tus ingresos, gastos y deudas para obtener un analisis.")
        st.divider()
        st.subheader("Descargar movimientos")

        st.date_input("Desde")
        st.date_input("Hasta", value=None)

        st.download_button(
            label="Descargar como CSV",
            data="placeholder_csv",
            file_name="movimientos.csv",
            mime="text/csv",
            disabled=True,
        )

        st.download_button(
            label="Descargar como JSON",
            data="placeholder_json",
            file_name="movimientos.json",
            mime="application/json",
            disabled=True,
        )


def render_forms() -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.subheader("Ingresos")
            ingreso_cat = st.radio(
                "Tipo de ingreso",
                ["Transferencia", "Debito", "Credito", "Efectivo"],
                key="ingreso_tipo",
                horizontal=True,
            )
            ingreso_monto = st.number_input(
                "Monto (ARS)", min_value=0.0, key="ingreso_monto", format="%.2f"
            )
            ingreso_comentario = st.text_input(
                "Comentario (opcional)", key="ingreso_comentario"
            )
            if st.button("Anadir ingreso"):
                if ingreso_monto > 0:
                    add_movement(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "type": "Ingreso",
                            "category": ingreso_cat,
                            "amount": ingreso_monto,
                            "comment": ingreso_comentario,
                        }
                    )
                    st.success("Ingreso anadido.")
                else:
                    st.warning("El monto debe ser mayor a cero.")

    with col2:
        with st.container(border=True):
            st.subheader("Gastos")
            gasto_cat = st.radio(
                "Categoria de gasto",
                ["Fijo", "Variable", "Discrecional", "Urgente"],
                key="gasto_tipo",
                horizontal=True,
            )
            gasto_monto = st.number_input(
                "Monto (ARS)", min_value=0.0, key="gasto_monto", format="%.2f"
            )
            gasto_comentario = st.text_input(
                "Comentario (opcional)", key="gasto_comentario"
            )
            if st.button("Anadir gasto"):
                if gasto_monto > 0:
                    add_movement(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "type": "Gasto",
                            "category": gasto_cat,
                            "amount": gasto_monto,
                            "comment": gasto_comentario,
                        }
                    )
                    st.success("Gasto anadido.")
                else:
                    st.warning("El monto debe ser mayor a cero.")

    with col3:
        with st.container(border=True):
            st.subheader("Deudas")
            deuda_cat = st.radio(
                "Tipo de deuda",
                ["Tarjeta de credito", "Prestamo", "Emergencia"],
                key="deuda_tipo",
                horizontal=True,
            )
            deuda_monto = st.number_input(
                "Monto (ARS)", min_value=0.0, key="deuda_monto", format="%.2f"
            )
            deuda_comentario = st.text_input(
                "Comentario (opcional)", key="deuda_comentario"
            )
            if st.button("Anadir deuda"):
                if deuda_monto > 0:
                    add_movement(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "type": "Urgente",
                            "category": deuda_cat,
                            "amount": deuda_monto,
                            "comment": deuda_comentario,
                        }
                    )
                    st.success("Deuda anadida.")
                else:
                    st.warning("El monto debe ser mayor a cero.")


def render_movements_table() -> None:
    st.subheader("Movimientos registrados en esta sesion")
    if st.session_state.movements:
        df = pd.DataFrame(st.session_state.movements)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aun no has anadido movimientos en esta sesion.")


def run_analysis(
    movements: List[Dict[str, Any]],
    shared_state: SharedState,
    team: AgentTeam,
) -> None:
    total_income = sum(m["amount"] for m in movements if m["type"] == "Ingreso")
    manual_expenses = {
        movement.get("comment") or movement.get("category"): movement.get("amount", 0)
        for movement in movements
        if movement["type"] == "Gasto"
    }
    debts = [
        {
            "name": movement.get("comment") or movement.get("category"),
            "amount": movement.get("amount", 0),
            "interest_rate": 0,
            "min_payment": 0,
        }
        for movement in movements
        if movement["type"] == "Urgente"
    ]

    financial_data = {
        "monthly_income": total_income,
        "manual_expenses": manual_expenses,
        "debts": debts,
    }

    advisor = FinanceAdvisorSystem()
    result = advisor.analyze_finances(financial_data)
    st.session_state.analysis_results = result
    save_movements_to_db(movements)
    st.session_state.movements = []

    shared_state.update_inputs(**financial_data)
    budget = result.get("budget_analysis")
    if isinstance(budget, BudgetAnalysis):
        shared_state.record_finding("budget", budget.dict())
        shared_state.record_plan("budget", budget.dict())
    shared_state.post_message(
        sender="ui.movements",
        type=MessageType.INFO,
        content="Analisis inicial ejecutado desde pestana de movimientos.",
        data={
            "movements_processed": len(movements),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    round_outputs = team.run_round(reason="analisis_finanzas")
    st.session_state.last_round_outputs = {
        key: value.dict() if value else None for key, value in round_outputs.items()
    }


def render_analysis_section(shared_state: SharedState, team: AgentTeam) -> None:
    if st.button("Analizar finanzas", type="primary", use_container_width=True):
        if not st.session_state.movements:
            st.warning("Por favor, anade al menos un movimiento antes de analizar.")
        else:
            with st.spinner("Analizando finanzas..."):
                try:
                    run_analysis(st.session_state.movements, shared_state, team)
                    st.success(
                        "Analisis completo. Los movimientos de esta sesion se guardaron en la base de datos."
                    )
                except Exception as exc:  # pragma: no cover - surface exception to UI
                    st.error(f"Ocurrio un error durante el analisis: {exc}")

    results = st.session_state.get("analysis_results")
    if isinstance(results, dict):
        budget = results.get("budget_analysis")
        if isinstance(budget, BudgetAnalysis):
            display_budget_analysis(budget)


def render_movimientos_tab(shared_state: SharedState, team: AgentTeam) -> None:
    render_forms()
    st.divider()
    render_movements_table()
    st.divider()
    render_analysis_section(shared_state, team)


def render_budget_tab(shared_state: SharedState) -> None:
    st.subheader("Resumen de presupuesto")
    data = shared_state.findings.get("budget")
    if data:
        try:
            budget = BudgetAnalysis(**data)
        except Exception:  # pragma: no cover - best effort display
            budget = None
        if budget:
            display_budget_analysis(budget)
            return
    st.info("Ejecuta un analisis para ver el presupuesto detallado.")


def render_savings_tab(shared_state: SharedState) -> None:
    st.subheader("Estrategia de ahorro")
    plan = shared_state.plans.get("savings")
    if not plan:
        st.info("Aun no hay recomendaciones de ahorro. Corre una ronda de analisis.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Excedente disponible", f"${plan.get('surplus', 0):,.2f}")
    col2.metric("Fondo emergencia", f"${plan.get('emergency_allocation', 0):,.2f}")
    col3.metric("Automatizaciones", f"${plan.get('automation_allocation', 0):,.2f}")

    st.markdown(
        "- 50% fondo emergencia\n- 30% automatizaciones\n- 20% metas flexibles"
    )


def render_debt_tab(shared_state: SharedState) -> None:
    st.subheader("Plan de deuda")
    plan = shared_state.plans.get("debt")
    if not plan:
        st.info("Aun no hay plan de deuda. Corre una ronda de analisis.")
        return

    col1, col2 = st.columns(2)
    col1.metric("Total deuda", f"${plan.get('total_debt', 0):,.2f}")
    col2.metric("Excedente", f"${plan.get('surplus', 0):,.2f}")

    st.table(
        pd.DataFrame(
            [
                {
                    "Estrategia": "Avalanche",
                    "Monto": plan.get("avalanche_payment", 0),
                },
                {
                    "Estrategia": "Snowball",
                    "Monto": plan.get("snowball_payment", 0),
                },
            ]
        )
    )


def render_ai_team_tab(shared_state: SharedState, team: AgentTeam) -> None:
    st.subheader("Chat con el Manager")
    with st.form("manager_chat_form"):
        user_message = st.text_area("Mensaje para el Manager", key="manager_chat_input")
        submitted = st.form_submit_button("Enviar mensaje")
        if submitted:
            message = user_message.strip()
            if message:
                team.send_user_message(message)
                st.success("Mensaje enviado al Manager.")
            else:
                st.warning("Escribe un mensaje antes de enviar.")

    conversation = [
        message
        for message in shared_state.log
        if message.sender in {"user", "manager"}
    ]
    if conversation:
        chat_container = st.container(border=True)
        for message in conversation[-20:]:
            author = "Usuario" if message.sender == "user" else "Manager"
            chat_container.markdown(f"**{author}:** {message.content}")
    else:
        st.info("Aun no hay mensajes en la conversacion.")

    st.subheader("Estado de objetivos")
    goals = shared_state.goals.dict()
    st.json(goals)

    st.subheader("Delegaciones del Manager")
    delegations = shared_state.plans.get("manager", {}).get("delegations", [])
    if delegations:
        st.table(pd.DataFrame(delegations))
    else:
        st.info("Sin delegaciones registradas por ahora.")

    st.subheader("Timeline del equipo")
    if st.button("Nueva ronda de analisis", key="trigger_new_round"):
        outputs = team.run_round(reason="manual_ui")
        st.session_state.last_round_outputs = {
            key: value.dict() if value else None for key, value in outputs.items()
        }
        st.success("Ronda ejecutada. El timeline se actualizo.")

    log_records = [
        {
            "timestamp": message.created_at.isoformat(timespec="seconds"),
            "sender": message.sender,
            "type": message.type.value,
            "to": message.to or "",
            "content": message.content,
            "data": json.dumps(message.data) if message.data else "",
        }
        for message in shared_state.log
    ]
    if not log_records:
        st.info("El bus de mensajes aun no tiene actividad.")
        return

    log_df = pd.DataFrame(log_records)
    senders = sorted(log_df["sender"].unique())
    types = sorted(log_df["type"].unique())

    filter_cols = st.columns(2)
    selected_senders = filter_cols[0].multiselect(
        "Agentes",
        options=senders,
        default=senders,
    )
    selected_types = filter_cols[1].multiselect(
        "Tipos",
        options=types,
        default=types,
    )

    mask = log_df["sender"].isin(selected_senders) & log_df["type"].isin(selected_types)
    st.dataframe(log_df[mask], use_container_width=True)

    if st.session_state.get("last_round_outputs"):
        with st.expander("Ultima ronda (mensajes emitidos)"):
            st.json(st.session_state.last_round_outputs)


def render_dashboard() -> None:
    ensure_session_state()
    shared_state = get_shared_state()
    team = get_agent_team()
    render_sidebar()
    st.title("Asesor Financiero - Argentina")

    tabs = st.tabs(
        [
            "Movimientos",
            "Presupuesto",
            "Ahorro",
            "Urgente",
            "Equipo IA",
        ]
    )

    with tabs[0]:
        render_movimientos_tab(shared_state, team)
    with tabs[1]:
        render_budget_tab(shared_state)
    with tabs[2]:
        render_savings_tab(shared_state)
    with tabs[3]:
        render_debt_tab(shared_state)
    with tabs[4]:
        render_ai_team_tab(shared_state, team)
