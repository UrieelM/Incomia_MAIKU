"""
Lambda 2: log_income
Endpoint: POST /users/{userId}/income

Core del producto. Registra un ingreso y recalcula el sueldo simulado,
la reserva y el estado de la reserva.
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.db import (
    get_user, put_transaction, update_user, put_alert,
    get_user_transactions,
)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

PAYMENTS_PER_MONTH = {"weekly": 4, "biweekly": 2, "monthly": 1}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_FIELDS", "userId es requerido en el path.")

        # Verificar que el usuario existe
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

        # ── PASO 1: Guardar la transacción ────────────────────────────────
        transaction_id = f"{str(uuid.uuid4())}#{date}"
        now = datetime.now(timezone.utc).isoformat()

        transaction = {
            "userId": user_id,
            "transactionId": transaction_id,
            "type": "income",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": "income",
            "category_label": "Ingreso",
            "date": date,
            "source": source,
            "notes": notes,
            "created_at": now,
        }
        put_transaction(transaction)

        # ── PASO 2: Recalcular simulated_salary ──────────────────────────
        salary_frequency = user.get("salary_frequency", "monthly")
        simulated_salary = _calculate_simulated_salary(user_id, salary_frequency)

        # ── PASO 3: Calcular excedente/déficit del mes actual ────────────
        current_month = date[:7]  # YYYY-MM
        reserve_balance = float(user.get("reserve_balance", 0))

        all_income = get_user_transactions(user_id, type_filter="income")
        ingreso_mes_actual = sum(
            float(t["amount"]) for t in all_income
            if t.get("date", "")[:7] == current_month
        )

        payments_this_month = PAYMENTS_PER_MONTH.get(salary_frequency, 1)
        expected_income = simulated_salary * payments_this_month
        diferencia = ingreso_mes_actual - expected_income

        if diferencia > 0:
            # Mes bueno: guarda 80% del excedente
            reserve_balance += diferencia * 0.8
        elif diferencia < 0:
            abs_diff = abs(diferencia)
            if reserve_balance >= abs_diff:
                reserve_balance += diferencia  # descuenta del reserve
            else:
                # Reserva insuficiente
                reserve_balance = 0
                _create_reserve_low_alert(user_id, now)

        # ── PASO 4: Actualizar reserve_status ────────────────────────────
        reserve_status = _calculate_reserve_status(reserve_balance, simulated_salary)

        # ── PASO 5: Actualizar usuario ────────────────────────────────────
        update_user(user_id, {
            "simulated_salary": Decimal(str(round(simulated_salary, 2))),
            "reserve_balance": Decimal(str(round(reserve_balance, 2))),
            "reserve_status": reserve_status,
        })

        # Construir mensaje
        freq_labels = {"weekly": "semanales", "biweekly": "quincenales", "monthly": "mensuales"}
        freq_label = freq_labels.get(salary_frequency, "mensuales")
        message = (
            f"Ingreso registrado. Tu sueldo simulado actualizado es "
            f"${simulated_salary:,.0f} {freq_label}."
        )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "transaction_id": transaction_id,
                "simulated_salary": round(simulated_salary, 2),
                "reserve_balance": round(reserve_balance, 2),
                "reserve_status": reserve_status,
                "message": message,
            }),
        }

    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("DYNAMODB_ERROR"):
            return _error(500, "DYNAMODB_ERROR", error_msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {error_msg}")


def _calculate_simulated_salary(user_id: str, salary_frequency: str) -> float:
    """
    Recalcula el simulated_salary con los ingresos de los últimos 6 meses.
    a. Obtiene TODOS los ingresos de los últimos 6 meses
    b. Agrupa por mes (YYYY-MM)
    c. Calcula el promedio mensual
    d. Divide según la frecuencia del usuario
    """
    now = datetime.now(timezone.utc)
    six_months_ago = (now - timedelta(days=180)).strftime("%Y-%m-%d")

    all_income = get_user_transactions(user_id, type_filter="income")
    recent_income = [
        t for t in all_income
        if t.get("date", "") >= six_months_ago
    ]

    if not recent_income:
        return 0.0

    # Agrupar por mes
    monthly_totals: dict[str, float] = defaultdict(float)
    for t in recent_income:
        month = t.get("date", "")[:7]  # YYYY-MM
        monthly_totals[month] += float(t["amount"])

    avg_monthly = sum(monthly_totals.values()) / len(monthly_totals)

    divisor = {"weekly": 4, "biweekly": 2, "monthly": 1}.get(salary_frequency, 1)
    return avg_monthly / divisor


def _calculate_reserve_status(reserve_balance: float, simulated_salary: float) -> str:
    """
    Calcula el estado de la reserva según cuántos meses cubre.
    meses_cubiertos = reserve_balance / simulated_salary
    >= 2 → green, >= 1 → yellow, < 1 → red
    """
    if simulated_salary <= 0:
        return "green" if reserve_balance > 0 else "red"

    meses_cubiertos = reserve_balance / simulated_salary
    if meses_cubiertos >= 2:
        return "green"
    elif meses_cubiertos >= 1:
        return "yellow"
    else:
        return "red"


def _create_reserve_low_alert(user_id: str, created_at: str) -> None:
    """Crea una alerta de reserva agotada."""
    alert_id = f"{str(uuid.uuid4())}#{created_at}"
    put_alert({
        "userId": user_id,
        "alertId": alert_id,
        "type": "reserve_low",
        "message": "Tu reserva se ha agotado. Tu sueldo simulado se ajustará este mes.",
        "data": {},
        "seen": False,
        "created_at": created_at,
    })


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
