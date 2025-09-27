from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    FINDING = "FINDING"
    ALERT = "ALERT"
    PROPOSAL = "PROPOSAL"
    QUESTION = "QUESTION"
    REBUTTAL = "REBUTTAL"
    DECISION = "DECISION"
    INFO = "INFO"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    type: MessageType
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    to: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class Goal(BaseModel):
    name: str
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0)
    horizon: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)


class GoalsState(BaseModel):
    objective: Optional[str] = None
    horizon: Optional[str] = None
    horizon_months: Optional[int] = None
    priorities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class Delegation(BaseModel):
    assignee: str
    task: str
    rationale: Optional[str] = None
    status: str = "pending"


class ManagerSummary(BaseModel):
    brief: str
    understood: List[str] = Field(default_factory=list)
    delegations: List[Delegation] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class SpendingCategory(BaseModel):
    category: str = Field(..., description="Expense category name")
    amount: float = Field(..., description="Amount spent in this category")


class BudgetAnalysis(BaseModel):
    total_expenses: float = Field(..., description="Total monthly expenses")
    monthly_income: Optional[float] = Field(None, description="Monthly income")
    spending_categories: List[SpendingCategory] = Field(
        ..., description="Breakdown of spending by category"
    )


class Debt(BaseModel):
    name: str = Field(..., description="Name of debt")
    amount: float = Field(..., description="Current balance")
    interest_rate: float = Field(..., description="Annual interest rate (%)")
    min_payment: Optional[float] = Field(None, description="Minimum monthly payment")
