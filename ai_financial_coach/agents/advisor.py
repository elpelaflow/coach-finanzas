from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.llm import ChatMessage, LLMClient
from ai_financial_coach.core.schemas import MessageType


class AdvisorAgent(BaseAgent):
    name = "advisor"
    role = "Human facing advisor"

    def __init__(
        self,
        state,
        *,
        system_prompt: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        prompt_name: Optional[str] = None,
    ) -> None:
        super().__init__(state, system_prompt=system_prompt)
        self.llm_client = llm_client
        self.prompt_name = prompt_name or "advisor_agent.txt"

    def tick(self):  # type: ignore[override]
        plans = self.state.plans
        findings = self.state.findings
        signature = f"{sorted(plans.keys())}|{sorted(findings.keys())}"
        if not plans and not findings:
            return None
        if not self.should_run(signature):
            return None

        payload = self._prepare_context(findings, plans)
        advisory = self._call_llm(payload) if self.llm_client else self._fallback_plan(payload)

        message = self.post(
            content=advisory["summary"],
            type=MessageType.INFO,
            data=advisory,
        )
        self.state.record_plan(self.name, advisory)
        return message

    def _prepare_context(self, findings: Dict[str, Any], plans: Dict[str, Any]) -> Dict[str, Any]:
        budget = findings.get("budget", {})
        savings = plans.get("savings", {})
        debt = plans.get("debt", {})
        investment = plans.get("investment", {})
        return {
            "goals": self.state.goals.dict(),
            "budget": budget,
            "savings": savings,
            "debt": debt,
            "investment": investment,
        }

    def _call_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        assert self.llm_client  # for typing only
        prompt = (
            "Toma el contexto financiero y devuelve un JSON valido con las claves: "
            "summary (string), plan_7_dias (lista de acciones), plan_30_dias (lista), plan_90_dias (lista), "
            "riesgos (lista), recomendaciones (lista). Usa un tono claro y accionable."
        )
        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(role="user", content=json.dumps(context, ensure_ascii=False)),
            ChatMessage(role="user", content=prompt),
        ]
        try:
            response_text, meta = self.llm_client.complete_with_metrics(messages, temperature=0.2)
            self._log_llm_meta(meta, ok=True)
            content = self._parse_json(response_text)
        except Exception as exc:  # pragma: no cover
            self._log_llm_meta({"error": str(exc), "model": getattr(self.llm_client, "model", "unknown")}, ok=False)
            content = self._fallback_plan(context)
        return content

    def _log_llm_meta(self, meta: Dict[str, Any], *, ok: bool) -> None:
        payload = {
            "ok": ok,
            "model": meta.get("model"),
            "latency": meta.get("latency"),
            "usage": meta.get("usage"),
            "error": meta.get("error"),
        }
        self.state.update_llm_status("advisor", **payload)
        status = "LLM_OK" if ok else "LLM_ERROR"
        content = f"{status} advisor ({payload.get('model', 'desconocido')})"
        if payload.get("latency"):
            content += f" - {payload['latency']:.2f}s"
        self.state.post_message(
            sender="llm.advisor",
            type=MessageType.INFO,
            content=content,
            data=payload,
        )

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(text[start : end + 1])
            else:
                raise
        return {
            "summary": data.get("summary", "Advisor: plan sintetico disponible."),
            "plan_7_dias": data.get("plan_7_dias", []),
            "plan_30_dias": data.get("plan_30_dias", []),
            "plan_90_dias": data.get("plan_90_dias", []),
            "riesgos": data.get("riesgos", []),
            "recomendaciones": data.get("recomendaciones", []),
        }

    def _fallback_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        budget = context.get("budget", {})
        savings = context.get("savings", {})
        debt = context.get("debt", {})
        summary_parts = []
        surplus = budget.get("surplus")
        if surplus is not None:
            summary_parts.append(f"Surplus estimado: {surplus:.2f} ARS")
        if debt.get("total_debt"):
            summary_parts.append(
                f"Deuda total estimada: {debt['total_debt']:.2f} ARS"
            )
        summary = "Advisor: " + ". ".join(summary_parts) if summary_parts else "Advisor: plan sugerido"
        plan_7 = [
            "Confirmar monto de excedente mensual y disponibilidad",
        ]
        plan_30 = []
        plan_90 = []
        if savings:
            plan_7.append("Abrir cuenta de ahorro para fondo de emergencia")
            plan_30.append("Automatizar transferencia para fondo de emergencia")
        if debt and debt.get("avalanche_payment"):
            plan_7.append("Asignar excedente a pagos tipo avalanche")
            plan_30.append("Recalcular pagos luego del primer mes")
            plan_90.append("Evaluar refinanciaciones una vez estabilizadas las deudas")
        recomendaciones = [
            "Revisar progreso cada 30 dias",
        ]
        return {
            "summary": summary,
            "plan_7_dias": plan_7,
            "plan_30_dias": plan_30,
            "plan_90_dias": plan_90,
            "riesgos": ["Ajustar gastos si el excedente cae"],
            "recomendaciones": recomendaciones,
        }

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
