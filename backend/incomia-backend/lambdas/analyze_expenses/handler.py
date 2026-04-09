"""
Lambda 5: analyze_expenses
Endpoint: POST /users/{userId}/analyze

Analiza los gastos de los últimos 30 días con Bedrock y genera una alerta
de tipo 'expense_pattern'. Solo se ejecuta una vez por semana por usuario.
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
    get_user, get_user_transactions, put_alert,
    get_alerts_by_type_and_date,
)

try:
    import weekly_alerts
except ImportError:
    weekly_alerts = None

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

ANALYSIS_SYSTEM = (
    "Eres un asesor financiero empático para freelancers en México. "
    "Tu tono es directo, útil y sin juicios. Responde ÚNICAMENTE con JSON válido."
)

ANALYSIS_USER_TEMPLATE = """Analiza los gastos de este freelancer de los últimos 30 días:

Gastos agrupados por comercio:
{expense_summary}

Sueldo simulado del usuario: ${simulated_salary} MXN {salary_frequency}

Responde con este JSON exacto:
{{
  "message": "mensaje de máximo 2 oraciones mencionando los 2-3 gastos más relevantes con montos específicos. Tono directo, sin regaños.",
  "top_merchants": [
    {{"merchant": "nombre", "count": número_de_visitas, "total": monto_total}}
  ],
  "total_secondary": monto_total_gastos_secundarios,
  "suggestion": "una sugerencia concreta y accionable en máximo 1 oración, con el ahorro potencial en pesos"
}}

REGLAS:
- Máximo 3 merchants en top_merchants
- El mensaje debe mencionar montos exactos
- La sugerencia debe incluir un número en pesos
- No uses palabras como 'debes', 'tienes que', 'deberías'"""


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

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # ── Verificar que no se haya ejecutado en los últimos 7 días ──────
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        existing_alerts = get_alerts_by_type_and_date(user_id, "expense_pattern", seven_days_ago)
        if existing_alerts:
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "alert_created": False,
                    "message": "Ya existe un análisis reciente (últimos 7 días). Intenta más tarde.",
                }),
            }

        # ── 1. Obtener transacciones de gastos de los últimos 30 días ─────
        thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        all_expenses = get_user_transactions(user_id, type_filter="expense")
        recent_expenses = [
            t for t in all_expenses
            if t.get("date", "") >= thirty_days_ago
        ]

        if not recent_expenses:
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "alert_created": False,
                    "message": "No hay gastos en los últimos 30 días para analizar.",
                }),
            }

        # ── 2. Agrupar por merchant ───────────────────────────────────────
        merchant_summary: dict[str, dict] = defaultdict(lambda: {"count": 0, "total": 0.0})
        total_secondary = 0.0

        for t in recent_expenses:
            merchant = t.get("merchant", "Desconocido")
            amount = float(t.get("amount", 0))
            merchant_summary[merchant]["count"] += 1
            merchant_summary[merchant]["total"] += amount
            if t.get("category") == "secondary":
                total_secondary += amount

        # Ordenar por total descendente para el prompt
        sorted_merchants = sorted(
            [{"merchant": k, **v} for k, v in merchant_summary.items()],
            key=lambda x: x["total"],
            reverse=True,
        )

        expense_summary_str = json.dumps(sorted_merchants[:10], ensure_ascii=False)
        salary_frequency = user.get("salary_frequency", "monthly")
        simulated_salary = float(user.get("simulated_salary", 0))

        # ── 3. Construir prompt y llamar a Bedrock ────────────────────────
        if weekly_alerts:
            # Invocar la logica avanzada de IA
            wa_response = weekly_alerts.lambda_handler({"recent_transactions": recent_expenses}, context)
            try:
                wa_body = json.loads(wa_response["body"])
                wa_data = wa_body.get("data", {})
            except Exception:
                wa_data = {}

            # Extraemos la informacion del formato del Motor de Alertas Semanales
            message = wa_data.get("weekly_alert", "Analisis avanzado de IA completado.")
            
            # Formatear top_merchants al formato esperado
            raw_top_merchants = wa_data.get("top_3_discretionary_expenses", [])
            top_merchants = [
                {
                    "merchant": m.get("merchant", "Local"),
                    "total": float(m.get("amount", 0)),
                    "count": 1 # no se tiene en el formato nuevo
                } for m in raw_top_merchants
            ][:3]
            
            suggestion = wa_data.get("salary_adjustment_suggestion", {}).get("reason", "Considera revisar tus gastos hormiga.")
            
            parsed = {
                "message": message,
                "top_merchants": top_merchants,
                "total_secondary": round(total_secondary, 2),
                "suggestion": suggestion,
            }
        else:
            # Fallback basico si el script no se encuentra
            top_3 = sorted_merchants[:3]
            message = (
                f"Tus principales gastos este mes: "
                + ", ".join(f"{m['merchant']} ${m['total']:,.0f}" for m in top_3)
            )
            parsed = {
                "message": message,
                "top_merchants": [
                    {"merchant": m["merchant"], "count": m["count"], "total": m["total"]}
                    for m in top_3
                ],
                "total_secondary": round(total_secondary, 2),
                "suggestion": "Revisar tus gastos secundarios podria ayudarte a ahorrar mas.",
            }

        # Limitar top_merchants a 3 (redundante pero seguro)
        top_merchants = parsed.get("top_merchants", [])[:3]
        parsed["top_merchants"] = top_merchants

        # ── 4. Guardar UNA alerta en incomia-alerts ───────────────────────
        alert_id = f"{str(uuid.uuid4())}#{now_iso}"
        alert_data = {
            "top_merchants": top_merchants,
            "total_secondary": parsed.get("total_secondary", round(total_secondary, 2)),
            "suggestion": parsed.get("suggestion", ""),
        }

        put_alert({
            "userId": user_id,
            "alertId": alert_id,
            "type": "expense_pattern",
            "message": parsed.get("message", "Análisis de gastos completado."),
            "data": alert_data,
            "seen": False,
            "created_at": now_iso,
        })

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "alert_created": True,
                "alert": {
                    "type": "expense_pattern",
                    "message": parsed.get("message", ""),
                    "data": alert_data,
                },
            }),
        }

    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("DYNAMODB_ERROR"):
            return _error(500, "DYNAMODB_ERROR", error_msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {error_msg}")


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
