from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class IncomeRequest(BaseModel):
    amount: float

class IncomeResponse(BaseModel):
    amount_processed: float
    artificial_salary_paid: float
    surplus_to_fund: float
    withdrawn_from_fund: float
    current_target: float
    remaining_fund: float
    resilience_indicator: float

class TransactionHistory(BaseModel):
    id: int
    amount: float
    target_salary_at_time: Optional[float]
    created_at: str

class BalanceResponse(BaseModel):
    current_target_salary: float
    available_fund: float
    resilience_indicator: float
    financial_health_status: str
    transactions: List[TransactionHistory]
