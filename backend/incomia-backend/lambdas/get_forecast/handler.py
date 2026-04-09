"""
Lambda: get_forecast
Endpoint: GET /users/{userId}/ai/forecast

Pronostica la liquidez a 14 días del usuario combinando:
  - Datos DynamoDB (esquema backend) → traducidos con shared/ai_adapter.py
  - Modelo Prophet o Moving Average (liquidity_forecast.py bundled)

Tras calcular el pronóstico emite un evento ForecastReady a EventBridge
para que el asesor IA (get_ai_advice) genere el consejo personalizado.

Trigger: API Gateway  GET /users/{userId}/ai/forecast
"""

import json
import os
import sys
import logging
import boto3

# ── Resolución de rutas ───────────────────────────────────────────────────────
# Local/dev: shared/ vive dos niveles arriba de este handler.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "../../"))

# Lambda en producción: el Layer se extrae a /opt/
# Con source_dir directo (sin carpeta python/) los módulos quedan en /opt/
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    sys.path.insert(0, "/opt")
    sys.path.insert(0, "/opt/python")

from shared.db import get_user, get_user_transactions
from shared.ai_adapter import (
    adapt_user,
    adapt_transactions,
    adapt_expenses,
    adapt_forecast_response,
)

# liquidity_forecast.py está bundleado en el mismo zip que este handler
try:
    from liquidity_forecast import predict_liquidity
    FORECAST_AVAILABLE = True
except ImportError as _e:
    logging.getLogger("incomia.get_forecast").warning(
        f"liquidity_forecast no disponible (numpy/prophet ausente?): {_e}"
    )
    FORECAST_AVAILABLE = False

# ── Configuración ─────────────────────────────────────────────────────────────
logger = logging.getLogger("incomia.get_forecast")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

EVENTBRIDGE_BUS = os.environ.get("EVENTBRIDGE_BUS_NAME", "incomia-events")
AWS_REGION      = os.environ.get("AWS_REGION_NAME", "us-east-1")

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type":                 "application/json",
}


# ── Handler principal ─────────────────────────────────────────────────────────

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_PARAM", "userId es requerido en el path.")

        # 1 ── Obtener datos de DynamoDB (esquema backend) ─────────────────
        db_user = get_user(user_id)
        if not db_user:
            return _error(404, "USER_NOT_FOUND", f"Usuario '{user_id}' no encontrado.")

        db_transactions = get_user_transactions(user_id)

        # 2 ── Traducir al esquema AI con el adaptador ─────────────────────
        ai_user         = adapt_user(db_user)
        ai_transactions = adapt_transactions(db_transactions)
        ai_expenses     = adapt_expenses(db_transactions)

        # 3 ── Ejecutar pronóstico ─────────────────────────────────────────
        if FORECAST_AVAILABLE:
            forecast_raw = predict_liquidity(ai_user, ai_transactions, ai_expenses)
        else:
            # Fallback mínimo cuando numpy no está disponible
            forecast_raw = _minimal_fallback(ai_user)

        # 4 ── Emitir ForecastReady a EventBridge ──────────────────────────
        _emit_forecast_event(forecast_raw, user_id)

        # 5 ── Formatear respuesta para el frontend ─────────────────────────
        response = adapt_forecast_response(forecast_raw)

        return {
            "statusCode": 200,
            "headers":    CORS_HEADERS,
            "body":       json.dumps(response, default=str, ensure_ascii=False),
        }

    except Exception as exc:
        logger.exception(f"Error en get_forecast para {event.get('pathParameters')}: {exc}")
        msg = str(exc)
        if "DYNAMODB_ERROR" in msg:
            return _error(500, "DYNAMODB_ERROR", msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {msg}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _emit_forecast_event(prediction: dict, user_id: str) -> None:
    """Publica ForecastReady en EventBridge para disparar el asesor IA."""
    try:
        p      = prediction.get("prediction", {})
        detail = {
            "event_type":             "ForecastReady",
            "user_id":                user_id,
            "risk_score":             p.get("new_risk_score", 50),
            "bankruptcy_probability": p.get("bankruptcy_probability", 0),
            "trigger_alert":          p.get("trigger_liquidity_alert", False),
            "model_used":             prediction.get("model_used", "unknown"),
        }
        eb = boto3.client("events", region_name=AWS_REGION)
        eb.put_events(Entries=[{
            "Source":       "incomia.liquidity-forecast",
            "DetailType":   "ForecastReady",
            "Detail":       json.dumps(detail, default=str),
            "EventBusName": EVENTBRIDGE_BUS,
        }])
        logger.info(f"ForecastReady emitido para {user_id}")
    except Exception as exc:
        # EventBridge falla → no bloquear la respuesta al cliente
        logger.warning(f"No se pudo emitir ForecastReady: {exc}")


def _minimal_fallback(ai_user: dict) -> dict:
    """Pronóstico simplificado cuando liquidity_forecast no está disponible."""
    from datetime import datetime, timedelta
    balance = float(ai_user.get("stabilization_fund_balance", 0))
    risk    = int(ai_user.get("current_risk_score", 50))

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    projection = [
        {
            "day":               d,
            "date":              (today + timedelta(days=d)).strftime("%Y-%m-%d"),
            "projected_balance": round(balance, 2),
        }
        for d in range(1, 15)
    ]

    return {
        "user_id":         ai_user.get("user_id"),
        "prediction_date": today.isoformat(),
        "horizon_days":    14,
        "model_used":      "static_fallback",
        "metrics": {
            "starting_balance":      round(balance, 2),
            "min_projected_balance": round(balance, 2),
            "min_balance_on_day":    0,
            "days_below_zero":       0,
            "first_negative_day":    None,
            "final_balance":         round(balance, 2),
            "bankruptcy_probability": 0.0,
        },
        "prediction": {
            "trigger_liquidity_alert": risk >= 70,
            "new_risk_score":          risk,
            "bankruptcy_probability":  0.0,
            "bankruptcy_threshold":    0.6,
            "min_projected_balance":   round(balance, 2),
            "min_balance_on_day":      0,
            "days_below_zero":         0,
            "first_negative_day":      None,
            "final_projected_balance": round(balance, 2),
        },
        "daily_projection": projection,
        "alert_message":    "[INFO] Pronóstico estático — numpy no disponible en este entorno.",
    }


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers":    CORS_HEADERS,
        "body":       json.dumps({"error": code, "message": message}),
    }
