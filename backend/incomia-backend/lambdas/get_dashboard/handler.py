"""
Lambda 4: get_dashboard
Endpoint: GET /users/{userId}/dashboard

Retorna una vista consolidada del usuario: datos financieros del mes actual,
próximo pago simulado y alertas no vistas.
"""
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.db import get_user, get_user_transactions, get_unseen_alerts

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_FIELDS", "userId es requerido en el path.")

        # ── 1. Obtener usuario ────────────────────────────────────────────
        user = get_user(user_id)
        if not user:
            return _error(404, "USER_NOT_FOUND", f"Usuario '{user_id}' no encontrado.")

        # ── 2. Obtener transacciones del mes actual ───────────────────────
        now = datetime.now(timezone.utc)
        current_month = now.strftime("%Y-%m")

        all_transactions = get_user_transactions(user_id)
        month_transactions = [
            t for t in all_transactions
            if t.get("date", "")[:7] == current_month
        ]

        # ── 3. Obtener alertas no vistas ─────────────────────────────────
        unseen_alerts = get_unseen_alerts(user_id)

        # ── 4. Calcular métricas del mes ─────────────────────────────────
        total_income_month = sum(
            float(t["amount"]) for t in month_transactions if t.get("type") == "income"
        )
        total_expenses_month = sum(
            float(t["amount"]) for t in month_transactions if t.get("type") == "expense"
        )
        primary_expenses = sum(
            float(t["amount"]) for t in month_transactions
            if t.get("type") == "expense" and t.get("category") == "primary"
        )
        secondary_expenses = sum(
            float(t["amount"]) for t in month_transactions
            if t.get("type") == "expense" and t.get("category") == "secondary"
        )

        # ── 5. Calcular próxima fecha de pago ─────────────────────────────
        salary_frequency = user.get("salary_frequency", "monthly")
        simulated_salary = float(user.get("simulated_salary", 0))
        next_payment = _calculate_next_payment(now, salary_frequency, simulated_salary)

        # ── 6. Serializar alertas (solo campos relevantes para UI) ────────
        alerts_serialized = [
            {
                "alertId": a.get("alertId", ""),
                "type": a.get("type", ""),
                "message": a.get("message", ""),
                "created_at": a.get("created_at", ""),
            }
            for a in unseen_alerts
        ]

        response_body = {
            "user": {
                "name": user.get("name", ""),
                "mode": user.get("mode", ""),
                "salary_frequency": salary_frequency,
                "simulated_salary": round(simulated_salary, 2),
                "reserve_balance": round(float(user.get("reserve_balance", 0)), 2),
                "reserve_status": user.get("reserve_status", "green"),
            },
            "current_month": {
                "total_income": round(total_income_month, 2),
                "total_expenses": round(total_expenses_month, 2),
                "primary_expenses": round(primary_expenses, 2),
                "secondary_expenses": round(secondary_expenses, 2),
            },
            "next_payment": next_payment,
            "unseen_alerts": alerts_serialized,
        }

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


def _calculate_next_payment(now: datetime, salary_frequency: str, simulated_salary: float) -> dict:
    """
    Calcula la próxima fecha de 'pago' según la frecuencia del usuario.
    - weekly:   próximo lunes
    - biweekly: día 1 o 16 del mes más cercano
    - monthly:  día 1 del próximo mes
    """
    today = now.date()

    if salary_frequency == "weekly":
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = today + timedelta(days=days_until_monday)

    elif salary_frequency == "biweekly":
        day = today.day
        if day < 16:
            # Próximo pago: día 16 de este mes
            next_date = today.replace(day=16)
        else:
            # Próximo pago: día 1 del siguiente mes
            if today.month == 12:
                next_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_date = today.replace(month=today.month + 1, day=1)

    else:  # monthly
        if today.month == 12:
            next_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_date = today.replace(month=today.month + 1, day=1)

    days_until = (next_date - today).days

    return {
        "date": next_date.isoformat(),
        "amount": round(simulated_salary, 2),
        "days_until": days_until,
    }


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
