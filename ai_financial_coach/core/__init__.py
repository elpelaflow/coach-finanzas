"""Core utilities for the multi-agent financial coach."""

from .base_agent import BaseAgent
from .database import fetch_data_from_db, init_db, save_movements_to_db
from .llm import ChatMessage, LLMClient, build_conversation
from .message_bus import MessageBus
from .schemas import (
    BudgetAnalysis,
    Debt,
    Delegation,
    Goal,
    GoalsState,
    ManagerSummary,
    Message,
    MessageType,
    SpendingCategory,
)
from .state import SharedState
from .system import FinanceAdvisorSystem

__all__ = [
    "BaseAgent",
    "BudgetAnalysis",
    "ChatMessage",
    "Debt",
    "Delegation",
    "FinanceAdvisorSystem",
    "Goal",
    "GoalsState",
    "LLMClient",
    "ManagerSummary",
    "Message",
    "MessageBus",
    "MessageType",
    "SharedState",
    "SpendingCategory",
    "build_conversation",
    "fetch_data_from_db",
    "init_db",
    "save_movements_to_db",
]
