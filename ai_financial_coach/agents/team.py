from __future__ import annotations

from typing import Dict, Optional

from ai_financial_coach.core.llm import ChatMessage, LLMClient
from ai_financial_coach.core.prompts import PromptLoader
from ai_financial_coach.core.schemas import GoalsState, Message, MessageType
from ai_financial_coach.core.state import SharedState

from .advisor import AdvisorAgent
from .budget import BudgetAgent
from .debt import DebtAgent
from .investment import InvestmentAgent
from .manager import ManagerAgent
from .savings import SavingsAgent


class AgentTeam:
    """Coordinates the specialist agents and the conversational manager."""

    def __init__(
        self, state: SharedState, loader: PromptLoader, *, llm_client: Optional[LLMClient] = None
    ) -> None:
        self.state = state
        self.loader = loader
        self.llm_client = llm_client
        self.shared_protocol = self.loader.load("00_shared_protocol")
        self.prompt_names: Dict[str, str] = {}

        def prompt(name: str) -> str:
            file_name = f"{name}.txt" if not name.endswith(".txt") else name
            self.prompt_names[name.replace("_agent", "")] = file_name
            body = self.loader.load(file_name)
            if self.shared_protocol:
                return f"{self.shared_protocol}\n\n{body}"
            return body

        self.manager = ManagerAgent(
            state,
            system_prompt=prompt("manager_agent"),
            llm_client=self.llm_client,
            prompt_name=self.prompt_names.get("manager"),
            on_goals_confirmed=self._auto_round_on_goals,
        )
        self.budget = BudgetAgent(state, system_prompt=prompt("budget_agent"))
        self.savings = SavingsAgent(state, system_prompt=prompt("savings_agent"))
        self.debt = DebtAgent(state, system_prompt=prompt("debt_agent"))
        self.investment = InvestmentAgent(state, system_prompt=prompt("investment_agent"))
        self.advisor = AdvisorAgent(
            state,
            system_prompt=prompt("advisor_agent"),
            llm_client=self.llm_client,
            prompt_name=self.prompt_names.get("advisor"),
        )

        self.specialists = [
            self.budget,
            self.savings,
            self.debt,
            self.investment,
        ]
        self.all_agents = self.specialists + [self.advisor, self.manager]

    def refresh_prompts(self) -> None:
        self.loader.refresh()
        self.shared_protocol = self.loader.load("00_shared_protocol")
        for agent, prompt_name in [
            (self.manager, "manager_agent"),
            (self.budget, "budget_agent"),
            (self.savings, "savings_agent"),
            (self.debt, "debt_agent"),
            (self.investment, "investment_agent"),
            (self.advisor, "advisor_agent"),
        ]:
            body = self.loader.load(f"{prompt_name}.txt" if not prompt_name.endswith(".txt") else prompt_name)
            full_prompt = f"{self.shared_protocol}\n\n{body}" if self.shared_protocol else body
            agent.configure(system_prompt=full_prompt)

    def get_prompt_metadata(self) -> Dict[str, str]:
        return dict(self.prompt_names)

    def get_llm_model(self) -> Optional[str]:
        return getattr(self.llm_client, "model", None) if self.llm_client else None

    def send_user_message(self, content: str) -> None:
        self.manager.handle_user_message(content)

    def update_goals(self, goals: GoalsState) -> None:
        self.manager.update_goals(goals)

    def run_round(self, *, reason: str = "manual") -> Dict[str, Optional[Message]]:
        self.state.post_message(
            sender="orchestrator",
            type=MessageType.INFO,
            content=f"Inicio de ronda: {reason}",
        )
        outputs: Dict[str, Optional[Message]] = {}
        for agent in self.specialists:
            outputs[agent.name] = agent.tick()
        outputs[self.advisor.name] = self.advisor.tick()
        outputs[self.manager.name] = self.manager.tick()
        return outputs

    def reset(self) -> None:
        for agent in self.all_agents:
            agent.reset()

    def probe_llm(self) -> Dict[str, Optional[str]]:
        if not self.llm_client:
            raise RuntimeError("LLM no configurado")
        messages = [
            ChatMessage(role="system", content="Eres un asistente de diagnostico. Responde en una palabra."),
            ChatMessage(role="user", content="Confirma la conexion respondiendo 'OK'."),
        ]
        try:
            text, meta = self.llm_client.complete_with_metrics(messages, temperature=0.0, max_tokens=10)
            response = text.strip().splitlines()[0] if text else ""
            payload = {
                "ok": True,
                "model": meta.get("model"),
                "latency": meta.get("latency"),
                "usage": meta.get("usage"),
                "response": response,
            }
            self.state.update_llm_status("probe", **payload)
            self.state.post_message(
                sender="llm.probe",
                type=MessageType.INFO,
                content=f"LLM_OK probe ({payload.get('model', 'desconocido')})",
                data=payload,
            )
            return payload
        except Exception as exc:  # pragma: no cover
            payload = {
                "ok": False,
                "model": getattr(self.llm_client, "model", "unknown"),
                "error": str(exc),
            }
            self.state.update_llm_status("probe", **payload)
            self.state.post_message(
                sender="llm.probe",
                type=MessageType.INFO,
                content=f"LLM_ERROR probe ({payload.get('model')})",
                data=payload,
            )
            return payload

    # ------------------------------------------------------------------
    def _auto_round_on_goals(self, goals: GoalsState) -> None:
        self.run_round(reason="goals_confirmed")
