from __future__ import annotations

from typing import Dict, Optional

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

    def __init__(self, state: SharedState, loader: PromptLoader) -> None:
        self.state = state
        self.loader = loader
        self.shared_protocol = self.loader.load("00_shared_protocol")

        def prompt(name: str) -> str:
            body = self.loader.load(name)
            if self.shared_protocol:
                return f"{self.shared_protocol}\n\n{body}"
            return body

        self.manager = ManagerAgent(state, system_prompt=prompt("manager_agent"))
        self.budget = BudgetAgent(state, system_prompt=prompt("budget_agent"))
        self.savings = SavingsAgent(state, system_prompt=prompt("savings_agent"))
        self.debt = DebtAgent(state, system_prompt=prompt("debt_agent"))
        self.investment = InvestmentAgent(state, system_prompt=prompt("investment_agent"))
        self.advisor = AdvisorAgent(state, system_prompt=prompt("advisor_agent"))

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
            body = self.loader.load(prompt_name)
            full_prompt = f"{self.shared_protocol}\n\n{body}" if self.shared_protocol else body
            agent.configure(system_prompt=full_prompt)

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
