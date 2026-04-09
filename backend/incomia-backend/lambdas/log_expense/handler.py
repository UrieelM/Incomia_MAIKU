"""
Lambda 3: log_expense
Endpoint: POST /users/{userId}/expense

Registra un gasto, lo clasifica con AWS Bedrock y lo guarda en DynamoDB.
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.db import get_user, put_transaction, update_transaction
from shared.bedrock import invoke_bedrock, parse_json_response

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

# Prompt para clasificación de gastos
CLASSIFICATION_SYSTEM = (
    "Eres un clasificador de gastos financieros para trabajadores "
    "independientes en México. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
)

CLASSIFICATION_USER_TEMPLATE = """Clasifica este gasto:
Merchant: {merchant}
Monto: ${amount} MXN
Notas del usuario: {notes}

Responde con este JSON exacto:
{{
  "category": "primary" o "secondary",
  "category_label": "una de estas opciones: Alimentación, Transporte, Renta y servicios, Salud, Educación, Cafeterías y restaurantes, Entretenimiento, Suscripciones, Compras en línea, Otro",
  "reasoning": "una línea explicando la clasificación"
}}

REGLAS:
- primary: gasto necesario para vivir o trabajar (renta, súper, gasolina, medicamentos, internet, herramientas de trabajo)
- secondary: gasto prescindible o de lujo (restaurantes, entretenimiento, ropa no esencial, suscripciones de streaming, cafeterías)
- Si las notas dicen que es para trabajo, clasifica como primary"""


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_FIELDS", "userId es requerido en el path.")

        # Verificar usuario
        user = get_user(user_id)
        if not user:
            return _error(404, "USER_NOT_FOUND", f"Usuario '{user_id}' no encontrado.")

        # Parsear body
        body = _parse_body(event)
        amount = body.get("amount")
        merchant = body.get("merchant", "").strip()
        date = body.get("date", "").strip()
        source = body.get("source", "manual")
        notes = body.get("notes", "")

        # Validaciones
        if amount is None:
            return _error(400, "MISSING_FIELDS", "El campo 'amount' es requerido.")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return _error(400, "INVALID_AMOUNT", "amount debe ser un número.")
        if amount <= 0:
            return _error(400, "INVALID_AMOUNT", "amount debe ser mayor que 0.")
        if not date:
            return _error(400, "MISSING_FIELDS", "El campo 'date' es requerido (ISO 8601).")

        now = datetime.now(timezone.utc).isoformat()

        # ── PASO 1: Guardar transacción con defaults ──────────────────────
        transaction_id = f"{str(uuid.uuid4())}#{date}"
        transaction = {
            "userId": user_id,
            "transactionId": transaction_id,
            "type": "expense",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": "secondary",      # default
            "category_label": "Otro",     # default
            "date": date,
            "source": source,
            "notes": notes,
            "created_at": now,
        }
        put_transaction(transaction)

        # ── PASO 2: Clasificar con Bedrock ────────────────────────────────
        category = "secondary"
        category_label = "Otro"
        bedrock_error = False

        try:
            prompt = CLASSIFICATION_USER_TEMPLATE.format(
                merchant=merchant or "Desconocido",
                amount=amount,
                notes=notes or "Sin notas",
            )
            raw_response = invoke_bedrock(prompt, system=CLASSIFICATION_SYSTEM)
            parsed = parse_json_response(raw_response)

            if parsed and "category" in parsed and "category_label" in parsed:
                if parsed["category"] in {"primary", "secondary"}:
                    category = parsed["category"]
                    category_label = parsed["category_label"]
            else:
                bedrock_error = True
        except Exception as e:
            print(f"[log_expense] Bedrock falló: {e}")
            bedrock_error = True

        # ── PASO 3: Actualizar la transacción con la clasificación ────────
        update_transaction(user_id, transaction_id, {
            "category": category,
            "category_label": category_label,
        })

        response_body = {
            "transaction_id": transaction_id,
            "category": category,
            "category_label": category_label,
            "message": "Gasto registrado y clasificado.",
        }
        if bedrock_error:
            response_body["warning"] = "BEDROCK_ERROR: clasificación por defecto aplicada."

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(response_body),
        }

    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("DYNAMODB_ERROR"):
            return _error(500, "DYNAMODB_ERROR", error_msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {error_msg}")


def _parse_body(event: dict) -> dict:
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body) if body else {}
    return body or {}


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
