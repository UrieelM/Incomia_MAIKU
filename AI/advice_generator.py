"""
Funcion AWS Lambda autocontenida que:
  1. Predice la liquidez a 14 dias (medias moviles).
  2. Invoca Claude 3 Sonnet via Amazon Bedrock para generar
     consejos financieros personalizados.
  3. Fallback robusto sin Bedrock para pruebas locales.

Autocontenido: no depende de archivos externos.
Deploy: Empaquetar como Lambda con capa boto3 actualizada.
Trigger: API Gateway POST /api/v1/advice

Uso local:
  python entregable_2_lambda_consejos_ia.py

Dependencias: numpy, boto3
Autor: Equipo Incomia
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np
import boto3
from botocore.exceptions import ClientError


# ════════════════════════════════════════════════════════════
# CONFIGURACION (inlined de config.py)
# ════════════════════════════════════════════════════════════

AWS_REGION = "us-east-1"

# Amazon Bedrock
BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
BEDROCK_MAX_TOKENS = 1024
BEDROCK_TEMPERATURE = 0.4
BEDROCK_ANTHROPIC_VERSION = "bedrock-2023-05-31"

# Motor de Prediccion
PREDICTION_HORIZON_DAYS = 14
MOVING_AVERAGE_WINDOW_DAYS = 30
LIQUIDITY_ALERT_THRESHOLD = 0.0
RISK_SCORE_HIGH = 80
RISK_SCORE_MEDIUM = 50

# Logger
logger = logging.getLogger("incomia_lambda")
logger.setLevel(logging.INFO)


# ════════════════════════════════════════════════════════════
# PARTE A: MOTOR DE PREDICCION DE LIQUIDEZ
# ════════════════════════════════════════════════════════════
# Evalua si un usuario esta en riesgo de quiebra en los
# proximos 14 dias usando medias moviles y proyeccion lineal.
# Modular: reemplazable por Prophet sin cambiar la interfaz.
# ════════════════════════════════════════════════════════════

def _parse_timestamp(ts: Any) -> datetime:
    """Convierte un timestamp (str o datetime) a datetime."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
        return datetime.strptime(ts[:10], "%Y-%m-%d")
    raise ValueError(f"Formato de timestamp no reconocido: {ts}")


def _get_daily_series(
    transactions: List[Dict[str, Any]],
    txn_type: str,
    window_days: int = MOVING_AVERAGE_WINDOW_DAYS,
) -> Dict[str, float]:
    """Agrupa transacciones por dia para los ultimos window_days dias."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=window_days)

    daily: Dict[str, float] = {}
    for i in range(window_days + 1):
        day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily[day] = 0.0

    for txn in transactions:
        if txn.get("type") != txn_type:
            continue
        txn_date = _parse_timestamp(txn["timestamp"])
        if txn_date < start_date:
            continue
        day_key = txn_date.strftime("%Y-%m-%d")
        if day_key in daily:
            val = abs(float(txn.get("amount", 0))) if txn_type == "gasto_variable" else float(txn.get("amount", 0))
            daily[day_key] += val

    return daily


def calculate_moving_average(daily_values: Dict[str, float], window: int = 7) -> float:
    """Calcula la media movil simple de los ultimos `window` dias."""
    sorted_days = sorted(daily_values.keys(), reverse=True)
    recent = sorted_days[:window]
    if not recent:
        return 0.0
    return float(np.mean([daily_values[d] for d in recent]))


def predict_liquidity(
    user: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
    horizon_days: int = PREDICTION_HORIZON_DAYS,
    window_days: int = MOVING_AVERAGE_WINDOW_DAYS,
) -> Dict[str, Any]:
    """
    Motor de prediccion de liquidez simplificado.
    Proyecta saldo dia a dia y genera alertas si cae <= 0.

    Args:
        user: Perfil del usuario (dict tipo User).
        transactions: Historial de transacciones.
        expenses: Gastos fijos del usuario.
        horizon_days: Dias a futuro a predecir (default: 14).
        window_days: Ventana de historia para media movil.

    Returns:
        Dict con prediccion completa, metricas y proyeccion dia a dia.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    user_id = user.get("user_id")
    user_txns = [t for t in transactions if t.get("user_id") == user_id]
    user_expenses = [e for e in expenses if e.get("user_id") == user_id and e.get("is_active", True)]

    # Medias moviles
    daily_income = _get_daily_series(user_txns, "ingreso", window_days)
    daily_var_expenses = _get_daily_series(user_txns, "gasto_variable", window_days)

    avg_daily_income = calculate_moving_average(daily_income, window=7)
    avg_daily_var_expense = calculate_moving_average(daily_var_expenses, window=14)
    avg_daily_income_30d = calculate_moving_average(daily_income, window=30)

    # Saldo inicial
    current_balance = float(user.get("stabilization_fund_balance", 0.0))
    total_fixed_monthly = sum(e.get("amount", 0) for e in user_expenses)
    estimated_cash = max(0, avg_daily_income_30d * 30 - total_fixed_monthly) * 0.3
    starting_balance = current_balance + estimated_cash

    # Proyeccion dia a dia
    projection: List[Dict[str, Any]] = []
    running_balance = starting_balance
    min_balance = running_balance
    min_balance_day = 0
    days_below_zero = 0
    first_negative_day: Optional[int] = None

    for day_offset in range(1, horizon_days + 1):
        future_date = today + timedelta(days=day_offset)
        future_day_of_month = future_date.day

        projected_income = avg_daily_income
        projected_var_expense = avg_daily_var_expense

        fixed_expenses_today = sum(
            e.get("amount", 0) for e in user_expenses
            if e.get("due_day_of_month") == future_day_of_month
        )

        daily_net = projected_income - projected_var_expense - fixed_expenses_today
        running_balance += daily_net

        if running_balance < min_balance:
            min_balance = running_balance
            min_balance_day = day_offset

        if running_balance <= LIQUIDITY_ALERT_THRESHOLD:
            days_below_zero += 1
            if first_negative_day is None:
                first_negative_day = day_offset

        projection.append({
            "day": day_offset,
            "date": future_date.strftime("%Y-%m-%d"),
            "projected_income": round(projected_income, 2),
            "projected_var_expense": round(projected_var_expense, 2),
            "fixed_expenses": round(fixed_expenses_today, 2),
            "daily_net": round(daily_net, 2),
            "projected_balance": round(running_balance, 2),
        })

    trigger_liquidity_alert = min_balance <= LIQUIDITY_ALERT_THRESHOLD

    new_risk_score = _calculate_risk_score(
        min_balance=min_balance, starting_balance=starting_balance,
        days_below_zero=days_below_zero, horizon_days=horizon_days,
        avg_daily_income=avg_daily_income, total_fixed_monthly=total_fixed_monthly,
        fund_balance=current_balance,
        resilience_goal_target=float(user.get("resilience_goal_target", 0)),
    )

    return {
        "user_id": user_id,
        "prediction_date": today.isoformat(),
        "horizon_days": horizon_days,
        "metrics": {
            "avg_daily_income_7d": round(avg_daily_income, 2),
            "avg_daily_income_30d": round(avg_daily_income_30d, 2),
            "avg_daily_variable_expense_14d": round(avg_daily_var_expense, 2),
            "total_fixed_monthly_expenses": round(total_fixed_monthly, 2),
            "starting_balance": round(starting_balance, 2),
            "stabilization_fund": round(current_balance, 2),
        },
        "prediction": {
            "trigger_liquidity_alert": trigger_liquidity_alert,
            "new_risk_score": new_risk_score,
            "min_projected_balance": round(min_balance, 2),
            "min_balance_on_day": min_balance_day,
            "days_below_zero": days_below_zero,
            "first_negative_day": first_negative_day,
            "final_projected_balance": round(running_balance, 2),
        },
        "daily_projection": projection,
        "alert_message": _build_alert_message(
            trigger_liquidity_alert, new_risk_score, min_balance,
            first_negative_day, user.get("primary_sector", "General"),
        ),
        "model_version": "moving_average_v1",
    }


def _calculate_risk_score(
    min_balance: float, starting_balance: float,
    days_below_zero: int, horizon_days: int,
    avg_daily_income: float, total_fixed_monthly: float,
    fund_balance: float, resilience_goal_target: float,
) -> int:
    """Score de riesgo compuesto 0-100. Mayor = mayor riesgo.
    Factores: cobertura (35%), saldo minimo (25%), dias negativos (20%), fondo (20%)."""
    scores: List[float] = []

    # Factor 1: Ratio de cobertura (35%)
    monthly_income = avg_daily_income * 30
    if total_fixed_monthly > 0:
        coverage = monthly_income / total_fixed_monthly
        s = 0 if coverage >= 2.0 else (20 if coverage >= 1.5 else (50 if coverage >= 1.0 else (80 if coverage >= 0.7 else 100)))
    else:
        s = 10
    scores.append(s * 0.35)

    # Factor 2: Saldo minimo proyectado (25%)
    if starting_balance > 0:
        ratio = min_balance / starting_balance
        s = 0 if ratio > 0.5 else (30 if ratio > 0.2 else (60 if ratio > 0 else 100))
    else:
        s = 90 if min_balance <= 0 else 50
    scores.append(s * 0.25)

    # Factor 3: Dias en negativo (20%)
    s = min(100, int((days_below_zero / horizon_days) * 200)) if horizon_days > 0 else 0
    scores.append(s * 0.20)

    # Factor 4: Fondo de estabilizacion (20%)
    if resilience_goal_target > 0:
        ratio = fund_balance / resilience_goal_target
        s = 0 if ratio >= 1.0 else (25 if ratio >= 0.5 else (50 if ratio >= 0.2 else (75 if ratio > 0 else 100)))
    else:
        s = 50
    scores.append(s * 0.20)

    return max(0, min(100, int(round(sum(scores)))))


def _build_alert_message(
    alert: bool, risk_score: int, min_balance: float,
    first_negative_day: Optional[int], sector: str,
) -> str:
    """Construye un mensaje de alerta legible para el frontend."""
    if not alert:
        if risk_score <= RISK_SCORE_MEDIUM:
            return (f"[OK] Tu liquidez se ve estable para las proximas 2 semanas. "
                    f"Score de riesgo: {risk_score}/100. Sigue asi.")
        else:
            return (f"[AVISO] Tu liquidez es ajustada pero no critica. "
                    f"Score de riesgo: {risk_score}/100. "
                    f"Considera recortar gastos variables esta semana.")

    urgency = "[ALERTA CRITICA]" if risk_score >= RISK_SCORE_HIGH else "[ALERTA]"
    day_msg = f"en {first_negative_day} dias" if first_negative_day else "proximamente"
    tips = {
        "Delivery": "Busca turnos extra en horas pico (12-2pm y 7-10pm) esta semana.",
        "Rideshare": "Considera activar horas nocturnas de viernes y sabado.",
        "Freelance_Dev": "Contacta clientes anteriores para proyectos rapidos o retainers.",
        "Freelance_Design": "Publica servicios rapidos (logos, banners) en Fiverr esta semana.",
    }
    tip = tips.get(sector, "Identifica fuentes de ingreso adicionales esta semana.")
    return (f"{urgency}: Tu saldo proyectado cae a ${min_balance:,.2f} MXN "
            f"{day_msg}. Score de riesgo: {risk_score}/100. "
            f"Accion sugerida: {tip}")


# ════════════════════════════════════════════════════════════
# PARTE B: SYSTEM PROMPT — Personalidad del Asesor Financiero
# ════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Eres "Incomia AI", un asesor financiero digital especializado en trabajadores de la economia gig (repartidores, conductores de plataforma, freelancers, trabajadores independientes) en Latinoamerica. Tu mision es ayudarles a estabilizar sus finanzas volatiles y construir resiliencia economica.

## Tu Personalidad
- **Empatico**: Entiendes que los ingresos irregulares generan estres. Nunca juzgas ni usas tono condescendiente.
- **Practico**: Tus consejos son accionables HOY, no teoricos. Entiendes que estas personas no tienen acceso a productos financieros tradicionales.
- **Directo**: Vas al punto. Usas lenguaje sencillo, sin jerga financiera innecesaria. Si usas un termino tecnico, lo explicas.
- **Motivador**: Reconoces logros pequenos. Un fondo de emergencia de $500 MXN ya es un avance.

## Reglas Estrictas
1. SIEMPRE analiza el contexto financiero antes de aconsejar: ingresos recientes, gastos fijos proximos, saldo del fondo de estabilizacion.
2. SIEMPRE incluye al menos UNA accion concreta que el usuario pueda hacer esta semana.
3. NUNCA recomiendes productos financieros de alto riesgo (criptomonedas, trading, prestamos informales).
4. Si el usuario esta en riesgo de liquidez (risk_score > 70), PRIORIZA alertas de gastos y negociacion de pagos.
5. Adapta tu consejo al sector del usuario (Delivery -> gestion de gasolina; Freelance -> diversificacion de clientes).
6. Responde SIEMPRE en espanol.
7. Usa un tono cercano y amigable, sin emojis.
8. Tu respuesta debe incluir estas secciones:
   - **Tu Panorama**: Resumen de la situacion financiera actual.
   - **Consejo Principal**: La accion mas importante ahora mismo.
   - **Plan de Accion** (2-3 puntos): Pasos concretos para las proximas 2 semanas.
   - **Meta del Mes**: Un objetivo alcanzable para el mes actual.

## Formato
Responde en texto plano con formato markdown ligero. Manten la respuesta entre 200-350 palabras para que sea digerible en la app movil."""


# ════════════════════════════════════════════════════════════
# PARTE C: CONSTRUCCION DEL PROMPT DE USUARIO
# ════════════════════════════════════════════════════════════

def build_user_prompt(
    user: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    upcoming_expenses: List[Dict[str, Any]],
) -> str:
    """Construye el prompt con contexto financiero completo."""
    income_txns = [t for t in recent_transactions if t.get("type") == "ingreso"]
    expense_txns = [t for t in recent_transactions if t.get("type") == "gasto_variable"]

    total_income_30d = sum(t["amount"] for t in income_txns)
    total_expenses_30d = sum(abs(t["amount"]) for t in expense_txns)
    total_fixed_expenses = sum(e["amount"] for e in upcoming_expenses if e.get("is_active", True))
    net_30d = total_income_30d - total_expenses_30d - total_fixed_expenses

    income_by_day: Dict[str, float] = {}
    for t in income_txns:
        day = t["timestamp"][:10] if isinstance(t["timestamp"], str) else t["timestamp"].strftime("%Y-%m-%d")
        income_by_day[day] = income_by_day.get(day, 0.0) + t["amount"]

    best_day = max(income_by_day, key=income_by_day.get) if income_by_day else "N/A"
    best_day_amount = income_by_day.get(best_day, 0.0)

    sources: Dict[str, float] = {}
    for t in income_txns:
        src = t.get("income_source", "Otros")
        sources[src] = sources.get(src, 0.0) + t["amount"]

    sources_text = "\n".join(
        [f"    - {src}: ${amt:,.2f} MXN" for src, amt in sorted(sources.items(), key=lambda x: -x[1])]
    ) or "    - Sin ingresos registrados"

    today = datetime.utcnow()
    expenses_text = "\n".join(
        [f"    - {e['name']}: ${e['amount']:,.2f} MXN (vence dia {e['due_day_of_month']})"
         for e in upcoming_expenses if e.get("is_active", True)]
    ) or "    - Sin gastos fijos registrados"

    return f"""Analiza la situacion financiera de este trabajador y dame tu consejo personalizado.

## Perfil del Usuario
- ID: {user.get('user_id', 'N/A')}
- Sector: {user.get('primary_sector', 'N/A')}
- Salario Artificial Calculado: ${user.get('artificial_salary', 0):,.2f} MXN/mes
- Fondo de Estabilizacion: ${user.get('stabilization_fund_balance', 0):,.2f} MXN
- Meta de Resiliencia: {user.get('resilience_goal_type', 'N/A')} (objetivo: ${user.get('resilience_goal_target', 0):,.2f} MXN)
- Score de Riesgo Actual: {user.get('current_risk_score', 0)}/100

## Ultimos 30 Dias (Resumen)
- Ingresos totales: ${total_income_30d:,.2f} MXN ({len(income_txns)} transacciones)
- Gastos variables: ${total_expenses_30d:,.2f} MXN ({len(expense_txns)} transacciones)
- Gastos fijos mensuales: ${total_fixed_expenses:,.2f} MXN
- Balance neto estimado: ${net_30d:,.2f} MXN
- Mejor dia de ingresos: {best_day} (${best_day_amount:,.2f} MXN)

## Fuentes de Ingreso (desglose)
{sources_text}

## Gastos Fijos Proximos
{expenses_text}

## Contexto Adicional
- Fecha actual: {today.strftime('%d de %B de %Y')}
- El usuario es un trabajador de la economia gig con ingresos variables.
- {"ALERTA: Score de riesgo ALTO (>" + "70). Priorizar consejos de supervivencia financiera." if user.get('current_risk_score', 0) > 70 else "El usuario tiene un riesgo manejable."}

Dame tu consejo personalizado siguiendo tu formato estandar."""


# ════════════════════════════════════════════════════════════
# PARTE D: INVOCACION A AMAZON BEDROCK
# ════════════════════════════════════════════════════════════

def invoke_bedrock(
    user: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    upcoming_expenses: List[Dict[str, Any]],
    model_id: str = BEDROCK_MODEL_ID,
) -> Dict[str, Any]:
    """Invoca Claude 3 Sonnet via Bedrock. Fallback si no hay credenciales."""
    user_prompt = build_user_prompt(user, recent_transactions, upcoming_expenses)

    request_body = {
        "anthropic_version": BEDROCK_ANTHROPIC_VERSION,
        "max_tokens": BEDROCK_MAX_TOKENS,
        "temperature": BEDROCK_TEMPERATURE,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    try:
        bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)
        logger.info(f"Invocando Bedrock modelo={model_id} para user={user.get('user_id')}")

        response = bedrock_client.invoke_model(
            modelId=model_id, contentType="application/json",
            accept="application/json", body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        advice_text = response_body["content"][0]["text"]

        return {
            "statusCode": 200,
            "advice": advice_text,
            "metadata": {
                "model_id": model_id,
                "user_id": user.get("user_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "input_tokens": response_body.get("usage", {}).get("input_tokens"),
                "output_tokens": response_body.get("usage", {}).get("output_tokens"),
                "risk_score": user.get("current_risk_score"),
            },
        }

    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.error(f"Error Bedrock: {error_message}")
        return {
            "statusCode": 500,
            "advice": _generate_fallback_advice(user, upcoming_expenses),
            "metadata": {"error": error_message, "fallback": True, "timestamp": datetime.utcnow().isoformat()},
        }

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return {
            "statusCode": 500,
            "advice": _generate_fallback_advice(user, upcoming_expenses),
            "metadata": {"error": str(e), "fallback": True, "timestamp": datetime.utcnow().isoformat()},
        }


# ════════════════════════════════════════════════════════════
# PARTE E: CONSEJO FALLBACK (Sin Bedrock)
# ════════════════════════════════════════════════════════════

def _generate_fallback_advice(
    user: Dict[str, Any],
    upcoming_expenses: List[Dict[str, Any]],
) -> str:
    """Genera consejo basico cuando Bedrock no esta disponible."""
    risk = user.get("current_risk_score", 50)
    fund = user.get("stabilization_fund_balance", 0)
    salary = user.get("artificial_salary", 0)
    total_fixed = sum(e["amount"] for e in upcoming_expenses if e.get("is_active", True))

    lines = [
        "**Tu Panorama**",
        f"Tu salario artificial es de ${salary:,.2f} MXN y tienes "
        f"${fund:,.2f} MXN en tu fondo de estabilizacion.", "",
    ]

    if risk > 70:
        lines.extend([
            "[ALERTA] Tu score de riesgo es alto. Es momento de priorizar lo esencial.", "",
            "**Consejo Principal**",
            f"Revisa tus gastos fijos y negocia plazos. Tienes ${total_fixed:,.2f} MXN en obligaciones mensuales.", "",
            "**Plan de Accion**",
            "1. Identifica el gasto fijo que puedas diferir esta quincena.",
            "2. Busca turnos extra en horas pico para cubrir la diferencia.",
            "3. No toques tu fondo de estabilizacion a menos que sea absolutamente necesario.",
        ])
    elif risk > 40:
        lines.extend([
            "**Consejo Principal**",
            f"Tu situacion es estable pero mejorable. Destina el 10% de cada ingreso (~${salary * 0.10:,.0f} MXN) a tu fondo.", "",
            "**Plan de Accion**",
            "1. Automatiza un ahorro del 10% tras cada ingreso.",
            "2. Revisa si hay suscripciones que puedas cancelar.",
            "3. Diversifica tus fuentes de ingreso si tu sector lo permite.",
        ])
    else:
        lines.extend([
            "**Consejo Principal**",
            f"Vas por buen camino. Enfocate en consolidar tu fondo hacia tu meta de ${user.get('resilience_goal_target', 0):,.2f} MXN.", "",
            "**Plan de Accion**",
            "1. Incrementa tu porcentaje de ahorro al 15-20% si es posible.",
            "2. Investiga opciones de inversion de bajo riesgo (CETES, fondos).",
            "3. Revisa si tu salario artificial refleja tu capacidad real.",
        ])

    lines.extend([
        "", "**Meta del Mes**",
        f"Aumentar tu fondo de estabilizacion en al menos ${salary * 0.05:,.0f} MXN.", "",
        "_Consejo generado localmente (modo offline)._",
    ])
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# PARTE F: HANDLER LAMBDA (punto de entrada AWS)
# ════════════════════════════════════════════════════════════

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler. Recibe perfil + transacciones + gastos,
    ejecuta prediccion de liquidez y genera consejo IA.

    Evento esperado (POST body desde API Gateway):
    {
        "user": { ... perfil User ... },
        "recent_transactions": [ ... Transaction ... ],
        "upcoming_expenses": [ ... Expense ... ]
    }
    """
    logger.info(f"Evento recibido: {json.dumps(event, default=str)[:500]}")

    # Parsear body
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif "body" in event:
            body = event["body"]
        else:
            body = event

        user = body["user"]
        recent_transactions = body.get("recent_transactions", [])
        upcoming_expenses = body.get("upcoming_expenses", [])

    except (KeyError, json.JSONDecodeError) as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Payload invalido. Se requiere: user, recent_transactions, upcoming_expenses.", "detail": str(e)}),
        }

    # Validar campos minimos
    required = ["user_id", "primary_sector", "current_risk_score"]
    missing = [f for f in required if f not in user]
    if missing:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Campos faltantes en user: {missing}"}),
        }

    # 1. Ejecutar prediccion de liquidez
    prediction = predict_liquidity(user, recent_transactions, upcoming_expenses)

    # 2. Invocar Bedrock (o fallback)
    advice_result = invoke_bedrock(user, recent_transactions, upcoming_expenses)

    # 3. Respuesta combinada
    return {
        "statusCode": advice_result["statusCode"],
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "advice": advice_result["advice"],
            "prediction": prediction,
            "metadata": advice_result["metadata"],
        }, default=str, ensure_ascii=False),
    }


# ════════════════════════════════════════════════════════════
# EJECUCION LOCAL (Testing)
# ════════════════════════════════════════════════════════════

def run_local_test():
    """Ejecuta prueba local con datos generados por el Entregable 1."""
    from data_generator import generate_all_data

    print("\n" + "=" * 60)
    print("  INCOMIA -- Lambda Consejos IA + Prediccion (test local)")
    print("=" * 60)

    data = generate_all_data(num_users=3, days_history=90)

    for user in data["users"]:
        uid = user["user_id"]
        txns = [t for t in data["transactions"] if t["user_id"] == uid]
        exps = [e for e in data["expenses"] if e["user_id"] == uid]

        print(f"\n{'─' * 60}")
        print(f"  {uid} | {user['primary_sector']} | Risk: {user['current_risk_score']}/100")
        print(f"{'─' * 60}")

        # Prediccion
        pred_result = predict_liquidity(user, txns, exps)
        pred = pred_result["prediction"]
        print(f"  Alerta liquidez: {'SI' if pred['trigger_liquidity_alert'] else 'NO'}")
        print(f"  Risk Score (predicho): {pred['new_risk_score']}/100")
        print(f"  Saldo min. proyectado: ${pred['min_projected_balance']:,.2f} MXN")
        print(f"  {pred_result['alert_message']}")

        # Consejo IA (usa fallback sin credenciales AWS)
        print(f"\n  -- Consejo IA --")
        advice_result = invoke_bedrock(user, txns, exps)
        print(f"  Status: {advice_result['statusCode']}")
        print(f"  Fallback: {advice_result.get('metadata', {}).get('fallback', False)}")
        print(f"\n{advice_result['advice']}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    run_local_test()
