"""
Lambda 6: inflation_alert
Endpoint: GET /users/{userId}/inflation

Calcula la inflación personalizada del usuario comparando su patrón de
gastos con los subíndices del INPC (vía API INEGI o fallback hardcodeado).
Crea una alerta si la inflación personal supera en 10% la nacional.
"""
import json
import uuid
import urllib.request
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
from shared.db import get_user, get_user_transactions, put_alert

try:
    import inflation_engine
except ImportError:
    inflation_engine = None

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

# Fallback de inflación por categoría (%)
INFLATION_FALLBACK = {
    "Alimentación": 4.8,
    "Transporte": 6.2,
    "Entretenimiento": 3.1,
    "Servicios": 5.5,
    "Nacional": 4.2,
}

# Mapeo de category_label → categoría de inflación
CATEGORY_TO_INFLATION = {
    "Alimentación": "Alimentación",
    "Transporte": "Transporte",
    "Renta y servicios": "Servicios",
    "Salud": "Servicios",
    "Educación": "Servicios",
    "Cafeterías y restaurantes": "Alimentación",
    "Entretenimiento": "Entretenimiento",
    "Suscripciones": "Entretenimiento",
    "Compras en línea": "Nacional",
    "Otro": "Nacional",
}

# Indicador INEGI INPC general (ID 628229)
INEGI_URL_TEMPLATE = (
    "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
    "INDICATOR/628229/es/BIE/2.0/{api_key}/json"
)

SSM_INEGI_KEY = "incomia/inegi_api_key"


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = (event.get("pathParameters") or {}).get("userId", "")
        if not user_id:
            return _error(400, "MISSING_FIELDS", "userId es requerido en el path.")

        user = get_user(user_id)
        if not user:
            return _error(404, "USER_NOT_FOUND", f"Usuario '{user_id}' no encontrado.")

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # ── 1. Obtener gastos de los últimos 3 meses ──────────────────────
        ninety_days_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        all_expenses = get_user_transactions(user_id, type_filter="expense")
        recent_expenses = [
            t for t in all_expenses
            if t.get("date", "") >= ninety_days_ago
        ]

        # Calcular peso porcentual por category_label
        category_totals: dict[str, float] = defaultdict(float)
        grand_total = 0.0

        for t in recent_expenses:
            label = t.get("category_label", "Otro")
            amount = float(t.get("amount", 0))
            category_totals[label] += amount
            grand_total += amount

        if grand_total == 0:
            # Sin gastos, no hay inflación personalizada que calcular
            national = _get_national_inflation()
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "national_inflation": national,
                    "personal_inflation": national,
                    "breakdown": [],
                    "alert": {"triggered": False, "message": "Sin gastos registrados en los últimos 3 meses."},
                }),
            }

        # Calcular pesos relativos y breakdown
        breakdown = []
        for label, total in category_totals.items():
            weight = total / grand_total
            inflation_category = CATEGORY_TO_INFLATION.get(label, "Nacional")
            inflation_rate = INFLATION_FALLBACK.get(inflation_category, INFLATION_FALLBACK["Nacional"])
            breakdown.append({
                "category": label,
                "weight": round(weight, 4),
                "inflation": inflation_rate,
            })

        # ── 3. Calcular inflación personalizada ───────────────────────────
        if inflation_engine:
            # Reconstruimos los gastos para inflation_engine
            user_expenses_mapped = { item["category"]: item["weight"] * grand_total for item in breakdown }
            calc_data = inflation_engine.calculate_personalized_inflation(user_expenses_mapped)
            personal_inflation = calc_data["personalized_inflation"]
            national_inflation = calc_data["national_inflation"]
        else:
            personal_inflation = sum(
                item["weight"] * item["inflation"] for item in breakdown
            )
            personal_inflation = round(personal_inflation, 2)

        # ── 4. Crear alerta si inflación personal > nacional * 1.1 ────────
        alert_result = {"triggered": False}
        simulated_salary = float(user.get("simulated_salary", 0))

        if personal_inflation > national_inflation * 1.1:
            ajuste = simulated_salary * (personal_inflation / 100)
            ajuste_rounded = round(ajuste, 0)

            message = (
                f"Tu inflación real es {personal_inflation}%, "
                f"mayor al promedio nacional de {national_inflation}%. "
                f"¿Ajustamos tu sueldo simulado ${ajuste_rounded:,.0f} más al mes?"
            )

            alert_id = f"{str(uuid.uuid4())}#{now_iso}"
            put_alert({
                "userId": user_id,
                "alertId": alert_id,
                "type": "inflation",
                "message": message,
                "data": {
                    "national_inflation": national_inflation,
                    "personal_inflation": personal_inflation,
                    "suggested_adjustment": ajuste_rounded,
                },
                "seen": False,
                "created_at": now_iso,
            })

            alert_result = {
                "triggered": True,
                "message": message,
                "suggested_adjustment": ajuste_rounded,
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "national_inflation": national_inflation,
                "personal_inflation": personal_inflation,
                "breakdown": breakdown,
                "alert": alert_result,
            }),
        }

    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("DYNAMODB_ERROR"):
            return _error(500, "DYNAMODB_ERROR", error_msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {error_msg}")


def _get_national_inflation() -> float:
    """
    Intenta obtener la inflación nacional desde SSM + API INEGI.
    Si falla, usa el fallback hardcodeado.
    """
    try:
        api_key = _get_ssm_parameter(SSM_INEGI_KEY)
        if not api_key:
            raise ValueError("API key no disponible en SSM")

        url = INEGI_URL_TEMPLATE.format(api_key=api_key)
        req = urllib.request.Request(url, headers={"User-Agent": "incomia-backend/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            # Extraer el último valor disponible del indicador
            series = data.get("Series", [{}])[0]
            obs = series.get("OBSERVATIONS", [])
            if obs:
                last_value = obs[-1].get("OBS_VALUE", INFLATION_FALLBACK["Nacional"])
                return float(last_value)
    except Exception as e:
        print(f"[inflation_alert] INEGI API falló: {e}. Usando fallback.")

    return INFLATION_FALLBACK["Nacional"]


def _get_ssm_parameter(parameter_name: str) -> str | None:
    """Obtiene un parámetro de AWS SSM Parameter Store."""
    try:
        import boto3
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"))
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except Exception as e:
        print(f"[inflation_alert] SSM error para '{parameter_name}': {e}")
        return None


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
