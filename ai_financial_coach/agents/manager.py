from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from ai_financial_coach.core.base_agent import BaseAgent
from ai_financial_coach.core.llm import ChatMessage, LLMClient
from ai_financial_coach.core.schemas import GoalsState, MessageType


ManagerCallback = Callable[[GoalsState], None]


class ManagerAgent(BaseAgent):
    name = "manager"
    role = "Conversational manager"

    def __init__(
        self,
        state,
        *,
        system_prompt: Optional[str] = None,
        goals: Optional[GoalsState] = None,
        llm_client: Optional[LLMClient] = None,
        prompt_name: Optional[str] = None,
        on_goals_confirmed: Optional[ManagerCallback] = None,
    ) -> None:
        super().__init__(state, system_prompt=system_prompt)
        self.goals = goals or GoalsState()
        self.llm_client = llm_client
        self.prompt_name = prompt_name or "manager_agent.txt"
        self.on_goals_confirmed = on_goals_confirmed
        self.history: List[ChatMessage] = []
        self._last_brief_count: int = 0

    # ------------------------------------------------------------------
    def handle_user_message(self, content: str) -> None:
        user_msg = ChatMessage(role="user", content=content)
        self.history.append(user_msg)
        self.state.post_message(
            sender="user",
            type=MessageType.INFO,
            content=f"Usuario -> Manager: {content[:80]}",
            data={"full_text": content},
        )

        llm_payload = self._call_llm()
        reply_text = llm_payload.get("reply") or "Estoy analizando la informacion, dame un momento."
        classification = llm_payload.get("classification", "INFO")
        questions = llm_payload.get("questions", [])

        message_type = MessageType.QUESTION if questions else MessageType.INFO
        self.post(
            content=reply_text,
            type=message_type,
            data={
                "classification": classification,
                "questions": questions,
            },
        )
        self.history.append(ChatMessage(role="assistant", content=reply_text))

        brief = llm_payload.get("brief") or {}
        delegations = brief.get("delegaciones", [])
        next_steps = brief.get("proximos_pasos", [])
        understood = brief.get("entendi", [])

        if delegations or next_steps:
            self.state.record_plan(
                "manager",
                {
                    "brief": brief,
                    "delegations": delegations,
                    "next_steps": next_steps,
                },
            )

        normalized_goals = llm_payload.get("normalized_goals")
        if normalized_goals:
            goals_state = self._build_goals_state(normalized_goals)
            self._publish_goals(goals_state, delegations, next_steps, understood)

    # ------------------------------------------------------------------
    def _call_llm(self) -> Dict[str, Any]:
        if not self.llm_client:
            return {}

        instructions = (
            "Analiza la conversacion y responde en JSON valido con las claves: "
            "classification (DATO|PREFERENCIA|DECISION|HIPOTESIS|PREGUNTA), "
            "needs_clarification (true/false), questions (lista de strings), "
            "reply (texto para el usuario), brief (objeto con listas 'tome_nota', 'entendi', 'delegaciones', 'proximos_pasos', y campos 'objetivo', 'horizonte'), "
            "delegaciones dentro de brief deben ser objetos con assignee, task, rationale, "
            "normalized_goals (objeto con objective, horizon_months, priorities, constraints). "
            "Si no tienes datos para algun campo, usa null o lista vacia."
        )
        messages = [ChatMessage(role="system", content=self.system_prompt)]
        messages.extend(self.history)
        messages.append(ChatMessage(role="user", content=instructions))

        try:
            response_text, meta = self.llm_client.complete_with_metrics(messages, temperature=0.2)
            self._log_llm_meta(meta, ok=True)
            return self._parse_json(response_text)
        except Exception as exc:  # pragma: no cover - network/runtime guard
            self._log_llm_meta({"error": str(exc), "model": getattr(self.llm_client, "model", "unknown")}, ok=False)
            fallback = {
                "reply": "Recibi tu mensaje. Estoy procesando la informacion del equipo.",
                "classification": "INFO",
                "questions": [],
            }
            return fallback

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                snippet = text[start : end + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    return {"reply": text.strip(), "classification": "INFO", "questions": []}
            return {"reply": text.strip(), "classification": "INFO", "questions": []}

    def _log_llm_meta(self, meta: Dict[str, Any], *, ok: bool) -> None:
        payload = {
            "ok": ok,
            "model": meta.get("model"),
            "latency": meta.get("latency"),
            "usage": meta.get("usage"),
            "error": meta.get("error"),
        }
        self.state.update_llm_status("manager", **payload)
        status = "LLM_OK" if ok else "LLM_ERROR"
        content = f"{status} manager ({payload.get('model', 'desconocido')})"
        if payload.get("latency"):
            content += f" - {payload['latency']:.2f}s"
        self.state.post_message(
            sender="llm.manager",
            type=MessageType.INFO,
            content=content,
            data=payload,
        )

    def _build_goals_state(self, data: Dict[str, Any]) -> GoalsState:
        return GoalsState(
            objective=data.get("objective"),
            horizon=data.get("horizon"),
            horizon_months=data.get("horizon_months"),
            priorities=data.get("priorities", []),
            constraints=data.get("constraints", []),
        )

    def _publish_goals(
        self,
        goals: GoalsState,
        delegations: List[Dict[str, str]],
        next_steps: List[str],
        understood: List[str],
    ) -> None:
        self.goals = goals
        self.state.set_goals(goals)
        decision_data = {
            "goals": goals.dict(),
            "delegations": delegations,
            "next_steps": next_steps,
            "entendi": understood,
        }
        summary = goals.objective or "sin objetivo"
        horizon_label = goals.horizon or (f"{goals.horizon_months} meses" if goals.horizon_months else "sin horizonte")
        self.post(
            content=f"Manager DECISION: objetivo {summary} ({horizon_label}).",
            type=MessageType.DECISION,
            data=decision_data,
        )
        self.state.record_plan(
            "manager",
            {
                "goals": goals.dict(),
                "delegations": delegations,
                "next_steps": next_steps,
                "entendi": understood,
            },
        )
        if self.on_goals_confirmed:
            self.on_goals_confirmed(goals)

    # ------------------------------------------------------------------
    def tick(self):  # type: ignore[override]
        findings_count = len(self.state.findings)
        if findings_count == 0 or findings_count == self._last_brief_count:
            return None

        summary = "+ ".join(sorted(self.state.findings.keys()))
        content = (
            "Manager: resumen de hallazgos disponibles -> "
            f"{summary if summary else 'sin hallazgos'}"
        )
        message = self.post(
            content=content,
            type=MessageType.INFO,
            data={"findings_count": findings_count},
        )
        self._last_brief_count = findings_count
        return message

    def reset(self) -> None:  # type: ignore[override]
        super().reset()
        self.history.clear()
        self._last_brief_count = 0




