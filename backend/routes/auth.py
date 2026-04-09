from fastapi import APIRouter
from models.schemas import LoginRequest

router = APIRouter()

@router.post("/login", tags=["auth"])
def login(request: LoginRequest):
    # Simulación de Cognito o servicio de identidad. No hay validación real para el MVP local.
    # Se genera un token dummy para el usuario.
    fake_token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_payload_for_{request.username}.signature"
    return {"access_token": fake_token, "token_type": "bearer"}
