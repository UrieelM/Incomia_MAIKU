"""
shared/ai_adapter.py — Puente de datos: modelo DynamoDB ↔ modelo IA

El backend principal (create_user, log_income, etc.) usa un esquema distinto
al que esperan los módulos del directorio AI/ (advice_generator, liquidity_forecast).

Este módulo traduce entre ambos esquemas sin modificar ninguno de los dos,
manteniendo la separación de responsabilidades.

Esquema DynamoDB (backend):
  userId, name, email, mode, salary_frequency,
  simulated_salary, reserve_balance, reserve_status

Esquema AI (esperado por advice_generator / liquidity_forecast):
  user_id, display_name, primary_sector, sub_sector,
  artificial_salary, stabilization_fund_balance,
  resilience_goal_target, current_risk_score, currency, city

Transacciones DynamoDB:
  userId, transactionId, type (income/expense),
  amount, merchant, category_label, date, source

Transacciones AI:
  user_id, transaction_id, timestamp, amount,
  type (ingreso/gasto_variable), income_source, description
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

# ── Mapeos de sectores ────────────────────────────────────────────────────────
# El campo `mode` del usuario determina el sector para la IA.
_MODE_TO_SECTOR = {
    "auto":        ("GigWorker",  "Gig_General"),
    "suggestion":  ("Freelance",  "Dev_Freelance"),
    "educational": ("Freelance",  "Freelance_General"),
}

# `reserve_status` (semáforo) → `current_risk_score` (0-100)
_RESERVE_STATUS_TO_RISK = {
    "green":  15,   # reserva cubre >2 meses → riesgo bajo
    "yellow": 55,   # reserva cubre 1-2 meses → riesgo medio
    "red":    82,   # reserva <1 mes → riesgo alto
}

# category_label del gasto → tipo AI
_EXPENSE_LABEL_TO_TYPE = {
    "Alimentación":         "gasto_variable",
    "Transporte":           "gasto_variable",
    "Cafeterías y restaurantes": "gasto_variable",
    "Entretenimiento":      "gasto_variable",
    "Suscripciones":        "gasto_variable",
    "Compras en línea":     "gasto_variable",
    "Otro":                 "gasto_variable",
    "Renta y servicios":    "gasto_fijo",
    "Salud":                "gasto_variable",
    "Educación":            "gasto_variable",
}


def _to_float(val: Any) -> float:
    """Convierte Decimal, str o int a float de forma segura."""
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def adapt_user(db_user: dict) -> dict:
    """
    Transforma el registro de usuario de DynamoDB al formato que esperan
    advice_generator.py y liquidity_forecast.py.

    Args:
        db_user: Ítem de la tabla incomia-users (PK: userId)

    Returns:
        Diccionario en formato AI.
    """
    mode = db_user.get("mode", "suggestion")
    primary_sector, sub_sector = _MODE_TO_SECTOR.get(mode, ("Freelance", "Freelance_General"))

    reserve_status = db_user.get("reserve_status", "yellow")
    risk_score = _RESERVE_STATUS_TO_RISK.get(reserve_status, 55)

    simulated_salary = _to_float(db_user.get("simulated_salary", 0))
    reserve_balance = _to_float(db_user.get("reserve_balance", 0))

    # Meta de resiliencia: 3 meses de sueldo simulado (mínimo $5,000 MXN)
    resilience_target = max(simulated_salary * 3, 5000.0)

    return {
        "user_id":                   db_user.get("userId", ""),
        "display_name":              db_user.get("name", "Usuario"),
        "primary_sector":            primary_sector,
        "sub_sector":                sub_sector,
        "artificial_salary":         simulated_salary,
        "stabilization_fund_balance": reserve_balance,
        "resilience_goal_type":      "3 meses de sueldo simulado",
        "resilience_goal_target":    resilience_target,
        "current_risk_score":        risk_score,
        "salary_frequency":          db_user.get("salary_frequency", "monthly"),
        "currency":                  "MXN",
        "city":                      "México",
        "profile_version":           "2026.1",
    }


def adapt_transactions(db_transactions: list) -> list:
    """
    Convierte transacciones de DynamoDB al formato AI.

    Los ingresos (type=income) → type="ingreso"
    Los gastos (type=expense)   → type="gasto_variable" (o "gasto_fijo" según label)

    El campo `merchant` se mapea a `income_source` / `description`.
    El campo `date` (YYYY-MM-DD) se convierte a timestamp ISO completo.
    """
    adapted = []
    for t in db_transactions:
        db_type = t.get("type", "")
        amount = _to_float(t.get("amount", 0))

        if db_type == "income":
            ai_type = "ingreso"
            income_source = t.get("merchant") or t.get("source") or "Ingreso"
            description = t.get("notes") or f"Ingreso de {income_source}"
        elif db_type == "expense":
            label = t.get("category_label", "Otro")
            ai_type = _EXPENSE_LABEL_TO_TYPE.get(label, "gasto_variable")
            income_source = ""
            description = t.get("merchant") or t.get("notes") or label
            # Los gastos van con signo negativo en el modelo AI
            amount = -abs(amount)
        else:
            continue  # Tipo desconocido, omitir

        # El transactionId tiene formato "uuid#YYYY-MM-DD"
        txn_id = t.get("transactionId", "")
        date_part = t.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

        # Construir timestamp ISO a partir de la fecha
        try:
            ts = datetime.strptime(date_part, "%Y-%m-%d").isoformat()
        except ValueError:
            ts = datetime.utcnow().isoformat()

        adapted.append({
            "transaction_id": txn_id,
            "user_id":        t.get("userId", ""),
            "timestamp":      ts,
            "amount":         amount,
            "currency":       "MXN",
            "type":           ai_type,
            "income_source":  income_source,
            "payment_method": t.get("source", "manual"),
            "description":    description,
            "category":       t.get("category_label", "Otro"),
        })

    return adapted


def adapt_expenses(db_transactions: list) -> list:
    """
    Deriva gastos fijos aproximados desde las transacciones de DynamoDB.
    El modelo AI necesita una lista de gastos recurrentes con `due_day_of_month`.

    Se agrupan los gastos de categoría primaria (renta, servicios) por merchant
    y se calcula el día de vencimiento promedio.

    Returns:
        Lista de gastos en formato AI (expense_id, name, amount, due_day_of_month, ...).
    """
    from collections import defaultdict

    # Solo gastos primarios (renta, servicios, salud, educación)
    PRIMARY_LABELS = {"Renta y servicios", "Salud", "Educación", "Transporte"}
    primary_by_merchant: dict[str, dict] = defaultdict(
        lambda: {"amounts": [], "days": [], "category": "servicios"}
    )

    for t in db_transactions:
        if t.get("type") != "expense":
            continue
        label = t.get("category_label", "")
        if label not in PRIMARY_LABELS:
            continue

        merchant = t.get("merchant") or label
        date_str = t.get("date", "")
        try:
            day = int(date_str.split("-")[2])
        except (IndexError, ValueError):
            day = 1

        primary_by_merchant[merchant]["amounts"].append(_to_float(t.get("amount", 0)))
        primary_by_merchant[merchant]["days"].append(day)
        primary_by_merchant[merchant]["category"] = label.lower().replace(" ", "_")

    fixed_expenses = []
    for i, (merchant, data) in enumerate(primary_by_merchant.items()):
        if not data["amounts"]:
            continue
        avg_amount = sum(data["amounts"]) / len(data["amounts"])
        avg_day = int(sum(data["days"]) / len(data["days"]))

        fixed_expenses.append({
            "expense_id":       f"EXP-AUTO-{i:04d}",
            "user_id":          "",   # se rellena en el handler
            "name":             merchant,
            "amount":           round(avg_amount, 2),
            "due_day_of_month": avg_day,
            "category":         data["category"],
            "is_active":        True,
            "currency":         "MXN",
        })

    return fixed_expenses


def adapt_forecast_response(forecast: dict) -> dict:
    """
    Normaliza la respuesta de predict_liquidity() para el frontend.
    Añade campos de UI y convierte probabilidades a porcentajes enteros.
    """
    if not forecast:
        return {}

    prediction = forecast.get("prediction", {})
    metrics = forecast.get("metrics", {})

    bp = prediction.get("bankruptcy_probability", 0)
    risk = prediction.get("new_risk_score", 50)

    # Nivel de riesgo semáforo
    if risk >= 70:
        risk_level = "high"
        risk_label = "Alto"
        risk_color = "red"
    elif risk >= 40:
        risk_level = "medium"
        risk_label = "Medio"
        risk_color = "yellow"
    else:
        risk_level = "low"
        risk_label = "Bajo"
        risk_color = "green"

    return {
        "model_used":           forecast.get("model_used", "unknown"),
        "horizon_days":         forecast.get("horizon_days", 14),
        "risk_score":           risk,
        "risk_level":           risk_level,
        "risk_label":           risk_label,
        "risk_color":           risk_color,
        "bankruptcy_probability": round(bp * 100, 1),   # % para UI
        "trigger_alert":        prediction.get("trigger_liquidity_alert", False),
        "alert_message":        forecast.get("alert_message", ""),
        "min_projected_balance": metrics.get("min_projected_balance", 0),
        "min_balance_on_day":   metrics.get("min_balance_on_day", 0),
        "final_balance":        metrics.get("final_balance", 0),
        "days_below_zero":      metrics.get("days_below_zero", 0),
        "daily_projection":     forecast.get("daily_projection", []),
        "prediction_date":      forecast.get("prediction_date", ""),
    }
