"""
Lambda: get_ai_advice
Endpoint: GET /users/{userId}/ai/advice

Genera consejo financiero personalizado invocando Amazon Bedrock (Nova Pro).
Combina el pronóstico de liquidez con el perfil del usuario para producir
recomendaciones accionables adaptadas al sector gig/freelance en México.

Soporta dos triggers:
  1. API Gateway  GET /users/{userId}/ai/advice
  2. EventBridge  ForecastReady (disparado automáticamente por get_forecast)

En el trigger EventBridge el consejo se genera en background; el resultado
no se devuelve al cliente sino que podría almacenarse en DynamoDB (alerts).
"""

import json
import os
import sys
import logging

# ── Resolución de rutas ───────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "../../"))
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    sys.path.insert(0, "/opt")
    sys.path.insert(0, "/opt/python")

from shared.db import get_user, get_user_transactions
from shared.ai_adapter import adapt_user, adapt_transactions, adapt_expenses

# advice_generator.py y liquidity_forecast.py están bundleados en este zip
try:
    from advice_generator import invoke_bedrock
    ADVICE_AVAILABLE = True
except ImportError as _e:
    logging.getLogger("incomia.get_ai_advice").warning(
        f"advice_generator no disponible: {_e}"
    )
    ADVICE_AVAILABLE = False

# ── Configuración ─────────────────────────────────────────────────────────────
logger = logging.getLogger("incomia.get_ai_advice")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type":                 "application/json",
}


# ── Handler principal ─────────────────────────────────────────────────────────

def lambda_handler(event, context):
    # CORS preflight
    http_method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method", "")
    )
    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        # ── Trigger EventBridge ForecastReady ─────────────────────────────
        if event.get("detail-type") == "ForecastReady":
            return _handle_eventbridge(event)

        # ── Trigger API Gateway ───────────────────────────────────────────
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_PARAM", "userId es requerido en el path.")

        return _generate_advice(user_id, forecast=None)

    except Exception as exc:
        logger.exception(f"Error en get_ai_advice: {exc}")
        return _error(500, "INTERNAL_ERROR", f"Error interno: {str(exc)}")


# ── Lógica central ────────────────────────────────────────────────────────────

def _handle_eventbridge(event: dict) -> dict:
    """Procesa el evento ForecastReady de EventBridge."""
    detail = event.get("detail", {})
    if isinstance(detail, str):
        detail = json.loads(detail)

    user_id = detail.get("user_id")
    if not user_id:
        logger.error("ForecastReady sin user_id.")
        return {"statusCode": 400, "body": json.dumps({"error": "user_id faltante."})}

    # Construir forecast parcial desde el payload del evento
    forecast_from_event = {
        "prediction": {
            "new_risk_score":         detail.get("risk_score", 50),
            "bankruptcy_probability":  detail.get("bankruptcy_probability", 0),
            "trigger_liquidity_alert": detail.get("trigger_alert", False),
        },
        "model_used": detail.get("model_used", "unknown"),
    }

    return _generate_advice(user_id, forecast=forecast_from_event)


def _generate_advice(user_id: str, forecast) -> dict:
    """
    Núcleo del handler:
      1. Obtiene datos DynamoDB.
      2. Adapta al esquema AI.
      3. Obtiene pronóstico completo si no viene del evento.
      4. Invoca Bedrock (con circuit breaker y fallback por reglas).
    """
    # 1 ── Datos DynamoDB ──────────────────────────────────────────────────
    db_user = get_user(user_id)
    if not db_user:
        return _error(404, "USER_NOT_FOUND", f"Usuario '{user_id}' no encontrado.")

    db_transactions = get_user_transactions(user_id)

    # 2 ── Adaptar al esquema AI ───────────────────────────────────────────
    ai_user         = adapt_user(db_user)
    ai_transactions = adapt_transactions(db_transactions)
    ai_expenses     = adapt_expenses(db_transactions)

    # 3 ── Obtener pronóstico si no viene del evento ───────────────────────
    if forecast is None:
        try:
            from liquidity_forecast import predict_liquidity
            forecast = predict_liquidity(ai_user, ai_transactions, ai_expenses)
        except Exception as exc:
            logger.warning(f"Pronóstico no disponible: {exc}. Continuando sin él.")
            forecast = None

    # 4 ── Generar consejo ─────────────────────────────────────────────────
    if not ADVICE_AVAILABLE:
        advice_text = _static_fallback(ai_user)
        metadata    = {"source": "static_fallback", "reason": "advice_generator_unavailable"}
    else:
        result      = invoke_bedrock(ai_user, ai_transactions, ai_expenses, forecast)
        advice_text = result.get("advice", "")
        metadata    = result.get("metadata", {})

    return {
        "statusCode": 200,
        "headers":    CORS_HEADERS,
        "body":       json.dumps({
            "advice":   advice_text,
            "metadata": metadata,
            "forecast": forecast,
        }, default=str, ensure_ascii=False),
    }


def _static_fallback(ai_user: dict) -> str:
    """Consejo mínimo cuando advice_generator no está disponible."""
    risk   = int(ai_user.get("current_risk_score", 50))
    fund   = float(ai_user.get("stabilization_fund_balance", 0))
    salary = float(ai_user.get("artificial_salary", 0))
    name   = ai_user.get("display_name", "Usuario")

    if risk >= 70:
        level = "**[ALERTA]** Tu riesgo financiero es alto."
        action = "Prioriza pagar renta y servicios básicos. Busca ingresos adicionales esta semana."
    elif risk >= 40:
        level = "Tu situación financiera es estable pero mejorable."
        action = f"Destina al menos el 10% de cada ingreso (~${salary * 0.10:,.0f} MXN) a tu fondo de estabilización."
    else:
        level = "Vas por muy buen camino. ¡Sigue así!"
        action = f"Enfócate en alcanzar tu meta de fondo. Actualmente tienes ${fund:,.0f} MXN."

    return (
        f"**Tu Panorama**\n"
        f"Hola {name}. {level} "
        f"Tu fondo de estabilización es de ${fund:,.2f} MXN y tu sueldo artificial es ${salary:,.2f} MXN/mes.\n\n"
        f"**Consejo Principal**\n{action}\n\n"
        f"**Plan de Acción**\n"
        f"1. Revisa tus gastos variables de los últimos 7 días.\n"
        f"2. Si tienes ingresos pendientes de cobrar, gestiónalos esta semana.\n"
        f"3. Considera CETES Directo para tu fondo (inversión mínima $100 MXN).\n\n"
        f"**Meta del Mes**\n"
        f"Incrementar tu fondo en ${max(salary * 0.05, 200):,.0f} MXN.\n\n"
        f"_Consejo generado en modo offline. Conecta Bedrock para consejos personalizados._"
    )


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers":    CORS_HEADERS,
        "body":       json.dumps({"error": code, "message": message}),
    }
