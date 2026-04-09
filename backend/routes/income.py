from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.schemas import IncomeRequest, IncomeResponse
from services.smoothing_algorithm import process_income_event
from db.database import engine
from models.domain import Base

router = APIRouter()

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # HTTPBearer valida automáticamente que haya un header Authorization con esquema Bearer
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Retornamos el user local 1 por ahora
    return 1

@router.post("/income", response_model=IncomeResponse, summary="Registrar ingreso", tags=["income"])
def register_income(
    request: IncomeRequest, 
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_current_user)
):
    """
    Registra un ingreso variable. En la versión AWS esto entraría a SQS o 
    directo a una Step Function. Aquí simulamos el flujo completo de forma síncrona/procedural.
    Flujo: Guardar -> Procesar Smooth -> Actualizar -> Responder.
    """
    result = process_income_event(db, user_id=user_id, amount=request.amount)
    return result
