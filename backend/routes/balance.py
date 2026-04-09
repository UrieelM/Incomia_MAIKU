from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.domain import FinancialState, Transaction
from models.schemas import BalanceResponse, TransactionHistory
from routes.income import get_current_user

router = APIRouter()

@router.get("/balance", response_model=BalanceResponse, summary="Obtener estado financiero", tags=["balance"])
def get_balance(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    financial_state = db.query(FinancialState).filter(FinancialState.user_id == user_id).first()
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).all()
    
    if not financial_state:
        return {
            "artificial_salary": 0.0,
            "available_fund": 0.0,
            "transactions": []
        }

    tx_history = [
        TransactionHistory(
            id=t.id,
            amount=t.amount,
            target_salary_at_time=t.target_salary_at_time,
            created_at=t.created_at.isoformat()
        ) for t in transactions
    ]

    resilience = 0.0
    status = "Viviendo al día (Sin colchón)"

    if financial_state.current_artificial_salary > 0:
        resilience = financial_state.available_fund / financial_state.current_artificial_salary

    if resilience >= 3.0:
        status = "Excelente (Alta resiliencia)"
    elif resilience >= 1.0:
        status = "Estable (Más de 1 mes cubierto)"
    elif resilience > 0.0:
        status = "En Riesgo (Colchón insuficiente)"

    return {
        "current_target_salary": financial_state.current_artificial_salary,
        "available_fund": financial_state.available_fund,
        "resilience_indicator": resilience,
        "financial_health_status": status,
        "transactions": tx_history
    }
