"""
Lambda 2: Pronostico de Liquidez con IA — Incomia (Equipo HAIKU)
================================================================
Microservicio independiente que predice el flujo de caja a 14 dias
usando Prophet (con fallback a medias moviles si Prophet no esta disponible).

Calcula la probabilidad de quiebra (saldo < 0) y dispara alerta
estructurada si el riesgo supera el 60%.

Arquitectura:
  - Trigger: EventBridge (DataIngested) o API Gateway GET /api/v1/forecast/{user_id}
  - Lee historial de DynamoDB
  - Ejecuta pronostico Prophet o fallback medias moviles
  - Emite evento ForecastReady a EventBridge

Tolerancia a fallos:
  Si Prophet falla (no converge, import error, timeout) → fallback a medias moviles.
  El response siempre incluye model_used: "prophet" | "moving_average_fallback"

Deploy: AWS Lambda con capa Prophet precompilada (o sin ella para fallback).
Dependencias: numpy, boto3, prophet (opcional)
Autor: Equipo HAIKU — Incomia
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

import numpy as np

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.config import Config as BotoConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Intentar importar Prophet — fallback si no disponible
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# Intentar importar pandas (requerido por Prophet)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ════════════════════════════════════════════════════════════
# LOGGING & CONFIGURACION
# ════════════════════════════════════════════════════════════
logger = logging.getLogger("incomia.liquidity_forecast")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s | %(message)s"))
    logger.addHandler(_h)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_USERS = os.environ.get("DYNAMODB_TABLE_USERS", "incomia_users")
DYNAMODB_TABLE_TRANSACTIONS = os.environ.get("DYNAMODB_TABLE_TRANSACTIONS", "incomia_transactions")
DYNAMODB_TABLE_EXPENSES = os.environ.get("DYNAMODB_TABLE_EXPENSES", "incomia_expenses")
EVENTBRIDGE_BUS = os.environ.get("EVENTBRIDGE_BUS_NAME", "incomia-events")
EVENTBRIDGE_SRC = os.environ.get("EVENTBRIDGE_SOURCE", "incomia.liquidity-forecast")

PREDICTION_HORIZON = int(os.environ.get("PREDICTION_HORIZON_DAYS", "14"))
MA_WINDOW = int(os.environ.get("MOVING_AVERAGE_WINDOW", "30"))
BANKRUPTCY_THRESHOLD = float(os.environ.get("BANKRUPTCY_THRESHOLD", "0.60"))
RISK_HIGH = 80
RISK_MEDIUM = 50


# ════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════

def _parse_ts(ts: Any) -> datetime:
    """Convierte timestamp (str o datetime) a datetime."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
        return datetime.strptime(ts[:10], "%Y-%m-%d")
    raise ValueError(f"Formato timestamp no reconocido: {ts}")


def _daily_series(transactions: List[Dict], txn_type: str, window: int = MA_WINDOW) -> Dict[str, float]:
    """Agrupa transacciones por dia para los ultimos window dias."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=window)
    daily = {}
    for i in range(window + 1):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        daily[day] = 0.0
    for t in transactions:
        if t.get("type") != txn_type:
            continue
        dt = _parse_ts(t["timestamp"])
        if dt < start:
            continue
        dk = dt.strftime("%Y-%m-%d")
        if dk in daily:
            val = abs(float(t.get("amount", 0))) if txn_type == "gasto_variable" else float(t.get("amount", 0))
            daily[dk] += val
    return daily


def _moving_avg(daily: Dict[str, float], window: int = 7) -> float:
    """Media movil simple de los ultimos window dias."""
    keys = sorted(daily.keys(), reverse=True)[:window]
    return float(np.mean([daily[k] for k in keys])) if keys else 0.0


# ════════════════════════════════════════════════════════════
# MOTOR PROPHET (Principal)
# ════════════════════════════════════════════════════════════

def _forecast_prophet(
    transactions: List[Dict],
    expenses: List[Dict],
    user: Dict[str, Any],
    horizon: int = PREDICTION_HORIZON,
) -> Optional[Dict[str, Any]]:
    """
    Pronostico con Prophet. Construye serie temporal de flujo neto diario.
    Incluye regresores: is_weekend, is_quincena.
    Retorna None si Prophet no esta disponible o falla.
    """
    if not PROPHET_AVAILABLE or not PANDAS_AVAILABLE:
        logger.warning("Prophet/pandas no disponible — usando fallback.")
        return None

    try:
        uid = user.get("user_id")
        user_txns = [t for t in transactions if t.get("user_id") == uid]

        if len(user_txns) < 14:
            logger.warning(f"Historial insuficiente para Prophet ({len(user_txns)} txns)")
            return None

        # Construir serie temporal de flujo neto diario
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=90)
        daily_net = {}
        for i in range(91):
            d = start + timedelta(days=i)
            daily_net[d.strftime("%Y-%m-%d")] = 0.0

        for t in user_txns:
            dt = _parse_ts(t["timestamp"])
            dk = dt.strftime("%Y-%m-%d")
            if dk in daily_net:
                daily_net[dk] += float(t.get("amount", 0))

        # Restar gastos fijos en su dia de vencimiento
        user_exp = [e for e in expenses if e.get("user_id") == uid and e.get("is_active", True)]
        for dk in daily_net:
            dom = int(dk.split("-")[2])
            for e in user_exp:
                if e.get("due_day_of_month") == dom:
                    daily_net[dk] -= float(e.get("amount", 0))

        # Crear DataFrame para Prophet
        dates = sorted(daily_net.keys())
        df = pd.DataFrame({
            "ds": pd.to_datetime(dates),
            "y": [daily_net[d] for d in dates],
        })

        # Regresores
        df["is_weekend"] = df["ds"].dt.dayofweek.isin([4, 5, 6]).astype(float)
        df["is_quincena"] = df["ds"].dt.day.isin([14, 15, 16, 29, 30, 31]).astype(float)

        # Ajustar modelo Prophet (silenciar logs de Stan)
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.80,
                changepoint_prior_scale=0.05,
            )
            model.add_regressor("is_weekend")
            model.add_regressor("is_quincena")
            model.fit(df)
        finally:
            sys.stdout = old_stdout

        # Generar futuro
        future = model.make_future_dataframe(periods=horizon)
        future["is_weekend"] = future["ds"].dt.dayofweek.isin([4, 5, 6]).astype(float)
        future["is_quincena"] = future["ds"].dt.day.isin([14, 15, 16, 29, 30, 31]).astype(float)
        forecast = model.predict(future)

        # Extraer pronostico (solo los dias futuros)
        future_fc = forecast.tail(horizon)
        projection = []
        balance = float(user.get("stabilization_fund_balance", 0))
        min_bal, min_day, days_neg = balance, 0, 0
        first_neg = None

        for i, (_, row) in enumerate(future_fc.iterrows()):
            day_offset = i + 1
            yhat = float(row["yhat"])
            yhat_lower = float(row["yhat_lower"])
            yhat_upper = float(row["yhat_upper"])
            balance += yhat
            lower_balance = balance - (yhat - yhat_lower)

            if balance < min_bal:
                min_bal = balance
                min_day = day_offset
            if balance <= 0:
                days_neg += 1
                if first_neg is None:
                    first_neg = day_offset

            projection.append({
                "day": day_offset,
                "date": row["ds"].strftime("%Y-%m-%d"),
                "yhat": round(yhat, 2),
                "yhat_lower": round(yhat_lower, 2),
                "yhat_upper": round(yhat_upper, 2),
                "projected_balance": round(balance, 2),
                "lower_bound_balance": round(lower_balance, 2),
            })

        # Calcular probabilidad de quiebra
        # P(quiebra) = proporcion de dias donde lower_bound_balance < 0
        neg_days_lower = sum(1 for p in projection if p["lower_bound_balance"] <= 0)
        bankruptcy_prob = neg_days_lower / horizon if horizon > 0 else 0.0

        return {
            "model_used": "prophet",
            "projection": projection,
            "metrics": {
                "starting_balance": round(float(user.get("stabilization_fund_balance", 0)), 2),
                "min_projected_balance": round(min_bal, 2),
                "min_balance_on_day": min_day,
                "days_below_zero": days_neg,
                "first_negative_day": first_neg,
                "final_balance": round(balance, 2),
                "bankruptcy_probability": round(bankruptcy_prob, 4),
            },
        }

    except Exception as e:
        logger.error(f"Prophet fallo: {e}")
        return None


# ════════════════════════════════════════════════════════════
# MOTOR FALLBACK (Medias Moviles)
# ════════════════════════════════════════════════════════════

def _forecast_moving_average(
    transactions: List[Dict],
    expenses: List[Dict],
    user: Dict[str, Any],
    horizon: int = PREDICTION_HORIZON,
) -> Dict[str, Any]:
    """
    Fallback: pronostico por medias moviles cuando Prophet no esta disponible.
    Siempre retorna un resultado valido.
    """
    uid = user.get("user_id")
    user_txns = [t for t in transactions if t.get("user_id") == uid]
    user_exp = [e for e in expenses if e.get("user_id") == uid and e.get("is_active", True)]

    daily_inc = _daily_series(user_txns, "ingreso", MA_WINDOW)
    daily_exp = _daily_series(user_txns, "gasto_variable", MA_WINDOW)

    avg_income_7d = _moving_avg(daily_inc, 7)
    avg_expense_14d = _moving_avg(daily_exp, 14)
    avg_income_30d = _moving_avg(daily_inc, 30)

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    balance = float(user.get("stabilization_fund_balance", 0))
    total_fixed = sum(float(e.get("amount", 0)) for e in user_exp)
    est_cash = max(0, avg_income_30d * 30 - total_fixed) * 0.3
    balance += est_cash

    projection = []
    min_bal, min_day, days_neg = balance, 0, 0
    first_neg = None

    for day_off in range(1, horizon + 1):
        future = today + timedelta(days=day_off)
        dom = future.day
        fixed_today = sum(float(e.get("amount", 0)) for e in user_exp if e.get("due_day_of_month") == dom)
        net = avg_income_7d - avg_expense_14d - fixed_today
        balance += net

        if balance < min_bal:
            min_bal = balance
            min_day = day_off
        if balance <= 0:
            days_neg += 1
            if first_neg is None:
                first_neg = day_off

        projection.append({
            "day": day_off,
            "date": future.strftime("%Y-%m-%d"),
            "projected_income": round(avg_income_7d, 2),
            "projected_var_expense": round(avg_expense_14d, 2),
            "fixed_expenses": round(fixed_today, 2),
            "daily_net": round(net, 2),
            "projected_balance": round(balance, 2),
        })

    # Probabilidad de quiebra estimada (simplificada)
    bankruptcy_prob = days_neg / horizon if horizon > 0 else 0.0

    return {
        "model_used": "moving_average_fallback",
        "projection": projection,
        "metrics": {
            "avg_daily_income_7d": round(avg_income_7d, 2),
            "avg_daily_income_30d": round(avg_income_30d, 2),
            "avg_daily_variable_expense_14d": round(avg_expense_14d, 2),
            "total_fixed_monthly": round(total_fixed, 2),
            "starting_balance": round(float(user.get("stabilization_fund_balance", 0)), 2),
            "min_projected_balance": round(min_bal, 2),
            "min_balance_on_day": min_day,
            "days_below_zero": days_neg,
            "first_negative_day": first_neg,
            "final_balance": round(balance, 2),
            "bankruptcy_probability": round(bankruptcy_prob, 4),
        },
    }


# ════════════════════════════════════════════════════════════
# FUNCION PRINCIPAL DE PRONOSTICO
# ════════════════════════════════════════════════════════════

def _calc_risk_score(metrics: Dict, user: Dict) -> int:
    """Score de riesgo compuesto 0-100."""
    scores = []
    # Factor cobertura (35%)
    fund = float(user.get("stabilization_fund_balance", 0))
    goal = float(user.get("resilience_goal_target", 1))
    ratio = fund / goal if goal > 0 else 0
    s = 0 if ratio >= 1.0 else (25 if ratio >= 0.5 else (50 if ratio >= 0.2 else (75 if ratio > 0 else 100)))
    scores.append(s * 0.35)

    # Factor saldo minimo (25%)
    start = metrics.get("starting_balance", 1)
    mn = metrics.get("min_projected_balance", 0)
    r = mn / start if start > 0 else -1
    s = 0 if r > 0.5 else (30 if r > 0.2 else (60 if r > 0 else 100))
    scores.append(s * 0.25)

    # Factor dias negativos (20%)
    dneg = metrics.get("days_below_zero", 0)
    s = min(100, int((dneg / PREDICTION_HORIZON) * 200)) if PREDICTION_HORIZON > 0 else 0
    scores.append(s * 0.20)

    # Factor probabilidad quiebra (20%)
    bp = metrics.get("bankruptcy_probability", 0)
    s = min(100, int(bp * 150))
    scores.append(s * 0.20)

    return max(0, min(100, int(round(sum(scores)))))


def _build_alert(metrics: Dict, risk: int, sector: str) -> str:
    """Construye mensaje de alerta."""
    bp = metrics.get("bankruptcy_probability", 0)
    mn = metrics.get("min_projected_balance", 0)
    fneg = metrics.get("first_negative_day")

    if bp < BANKRUPTCY_THRESHOLD and mn > 0:
        if risk <= RISK_MEDIUM:
            return (f"[OK] Liquidez estable para las proximas 2 semanas. "
                    f"Score: {risk}/100. Prob. quiebra: {bp:.0%}.")
        return (f"[AVISO] Liquidez ajustada. Score: {risk}/100. "
                f"Prob. quiebra: {bp:.0%}. Considera recortar gastos.")

    tips = {
        "Delivery": "Activa horas nocturnas viernes/sabado y busca bonos de plataforma.",
        "Freelance": "Contacta clientes anteriores para proyectos rapidos o adelantos.",
        "GigWorker": "Busca eventos/trabajos extra esta semana para cubrir la diferencia.",
    }
    tip = tips.get(sector, "Identifica fuentes de ingreso adicionales esta semana.")
    urgency = "[ALERTA CRITICA]" if risk >= RISK_HIGH else "[ALERTA]"
    day_msg = f"en {fneg} dias" if fneg else "proximamente"

    return (f"{urgency} Riesgo de quiebra: {bp:.0%}. Saldo minimo proyectado: "
            f"${mn:,.2f} MXN {day_msg}. Score: {risk}/100. Accion: {tip}")


def predict_liquidity(
    user: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
    horizon: int = PREDICTION_HORIZON,
) -> Dict[str, Any]:
    """
    Funcion principal de pronostico. Intenta Prophet primero, fallback a medias moviles.
    Calcula probabilidad de quiebra y genera alerta si > 60%.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    uid = user.get("user_id")

    # Intentar Prophet
    result = _forecast_prophet(transactions, expenses, user, horizon)

    # Fallback si Prophet fallo
    if result is None:
        logger.info(f"Usando fallback medias moviles para {uid}")
        result = _forecast_moving_average(transactions, expenses, user, horizon)

    # Calcular risk score y alerta
    metrics = result["metrics"]
    risk = _calc_risk_score(metrics, user)
    bp = metrics["bankruptcy_probability"]
    trigger_alert = bp >= BANKRUPTCY_THRESHOLD

    sector = user.get("primary_sector", "General")
    alert_msg = _build_alert(metrics, risk, sector)

    return {
        "user_id": uid,
        "prediction_date": today.isoformat(),
        "horizon_days": horizon,
        "model_used": result["model_used"],
        "metrics": metrics,
        "prediction": {
            "trigger_liquidity_alert": trigger_alert,
            "new_risk_score": risk,
            "bankruptcy_probability": round(bp, 4),
            "bankruptcy_threshold": BANKRUPTCY_THRESHOLD,
            "min_projected_balance": metrics["min_projected_balance"],
            "min_balance_on_day": metrics["min_balance_on_day"],
            "days_below_zero": metrics["days_below_zero"],
            "first_negative_day": metrics["first_negative_day"],
            "final_projected_balance": metrics["final_balance"],
        },
        "daily_projection": result["projection"],
        "alert_message": alert_msg,
    }


# ════════════════════════════════════════════════════════════
# DYNAMODB — Leer datos del usuario
# ════════════════════════════════════════════════════════════

def _decimal_to_float(obj: Any) -> Any:
    """Convierte Decimal a float recursivamente."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decimal_to_float(i) for i in obj]
    return obj


def _fetch_user_data(user_id: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """Lee perfil, transacciones y gastos de DynamoDB para un usuario."""
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 no disponible.")

    cfg = BotoConfig(region_name=AWS_REGION, retries={"max_attempts": 3, "mode": "exponential"})
    ddb = boto3.resource("dynamodb", config=cfg)

    # Perfil
    tbl_users = ddb.Table(DYNAMODB_TABLE_USERS)
    resp = tbl_users.get_item(Key={"user_id": user_id})
    user = _decimal_to_float(resp.get("Item", {}))
    if not user:
        raise ValueError(f"Usuario {user_id} no encontrado.")

    # Transacciones (Query con GSI o Scan filtrado)
    tbl_txns = ddb.Table(DYNAMODB_TABLE_TRANSACTIONS)
    txns = []
    scan_kwargs = {"FilterExpression": "user_id = :uid", "ExpressionAttributeValues": {":uid": user_id}}
    while True:
        resp = tbl_txns.scan(**scan_kwargs)
        txns.extend(_decimal_to_float(resp.get("Items", [])))
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    # Gastos
    tbl_exp = ddb.Table(DYNAMODB_TABLE_EXPENSES)
    exps = []
    scan_kwargs = {"FilterExpression": "user_id = :uid", "ExpressionAttributeValues": {":uid": user_id}}
    while True:
        resp = tbl_exp.scan(**scan_kwargs)
        exps.extend(_decimal_to_float(resp.get("Items", [])))
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    return user, txns, exps


# ════════════════════════════════════════════════════════════
# EVENTBRIDGE — Emitir ForecastReady
# ════════════════════════════════════════════════════════════

def _emit_forecast_event(prediction: Dict[str, Any]) -> Optional[Dict]:
    """Emite evento ForecastReady a EventBridge."""
    if not BOTO3_AVAILABLE:
        return None
    try:
        eb = boto3.client("events", region_name=AWS_REGION)
        detail = {
            "event_type": "ForecastReady",
            "user_id": prediction["user_id"],
            "risk_score": prediction["prediction"]["new_risk_score"],
            "bankruptcy_probability": prediction["prediction"]["bankruptcy_probability"],
            "trigger_alert": prediction["prediction"]["trigger_liquidity_alert"],
            "model_used": prediction["model_used"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        resp = eb.put_events(Entries=[{
            "Source": EVENTBRIDGE_SRC, "DetailType": "ForecastReady",
            "Detail": json.dumps(detail, default=str),
            "EventBusName": EVENTBRIDGE_BUS,
        }])
        logger.info(f"Evento ForecastReady emitido: user={prediction['user_id']}")
        return resp
    except Exception as e:
        logger.error(f"Error EventBridge: {e}")
        return None


# ════════════════════════════════════════════════════════════
# LAMBDA HANDLER
# ════════════════════════════════════════════════════════════

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler.
    Triggers:
      1. EventBridge DataIngested → procesa todos los user_ids del evento
      2. API Gateway GET → procesa user_id del path/query
      3. Invocacion directa con payload {user, transactions, expenses}
    """
    logger.info("Lambda liquidity_forecast invocada.")

    try:
        # Caso 1: EventBridge trigger
        if event.get("detail-type") == "DataIngested":
            detail = event.get("detail", {})
            if isinstance(detail, str):
                detail = json.loads(detail)
            user_ids = detail.get("user_ids", [])
            results = {}
            for uid in user_ids:
                try:
                    user, txns, exps = _fetch_user_data(uid)
                    pred = predict_liquidity(user, txns, exps)
                    _emit_forecast_event(pred)
                    results[uid] = pred
                except Exception as e:
                    logger.error(f"Error procesando {uid}: {e}")
                    results[uid] = {"error": str(e)}
            return {"statusCode": 200, "body": json.dumps(results, default=str, ensure_ascii=False)}

        # Caso 2: API Gateway
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        user_id = path_params.get("user_id") or query_params.get("user_id")

        if user_id:
            user, txns, exps = _fetch_user_data(user_id)
            pred = predict_liquidity(user, txns, exps)
            _emit_forecast_event(pred)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(pred, default=str, ensure_ascii=False),
            }

        # Caso 3: Invocacion directa con datos en payload
        body = event
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif isinstance(event.get("body"), dict):
            body = event["body"]

        user = body.get("user", {})
        txns = body.get("recent_transactions", body.get("transactions", []))
        exps = body.get("upcoming_expenses", body.get("expenses", []))

        if not user.get("user_id"):
            return {"statusCode": 400, "body": json.dumps({"error": "user_id requerido."})}

        pred = predict_liquidity(user, txns, exps)
        _emit_forecast_event(pred)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(pred, default=str, ensure_ascii=False),
        }

    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# ════════════════════════════════════════════════════════════
# EJECUCION LOCAL (Testing)
# ════════════════════════════════════════════════════════════

def run_local_test():
    """Prueba local con datos del data_generator."""
    from data_generator import generate_all_data

    print("\n" + "=" * 65)
    print("  INCOMIA — Lambda Pronostico Liquidez (test local)")
    print("=" * 65)
    print(f"  Prophet disponible: {'SI' if PROPHET_AVAILABLE else 'NO (usando fallback medias moviles)'}")
    print(f"  Pandas disponible:  {'SI' if PANDAS_AVAILABLE else 'NO'}")

    data = generate_all_data(num_users=4, days=90)

    for user in data["users"]:
        uid = user["user_id"]
        txns = [t for t in data["transactions"] if t["user_id"] == uid]
        exps = [e for e in data["expenses"] if e["user_id"] == uid]

        print(f"\n{'─' * 65}")
        print(f"  {uid} | {user['display_name']} | {user['primary_sector']}/{user['sub_sector']}")
        print(f"{'─' * 65}")

        pred = predict_liquidity(user, txns, exps)
        p = pred["prediction"]
        m = pred["metrics"]

        print(f"  Modelo usado:            {pred['model_used']}")
        print(f"  Prob. quiebra:           {p['bankruptcy_probability']:.1%}")
        print(f"  Umbral alerta:           {p['bankruptcy_threshold']:.0%}")
        print(f"  Alerta disparada:        {'SI' if p['trigger_liquidity_alert'] else 'NO'}")
        print(f"  Risk Score:              {p['new_risk_score']}/100")
        print(f"  Saldo min. proyectado:   ${p['min_projected_balance']:,.2f} MXN (dia {p['min_balance_on_day']})")
        print(f"  Saldo final proyectado:  ${p['final_projected_balance']:,.2f} MXN")
        print(f"  Dias en negativo:        {p['days_below_zero']}")
        print(f"\n  {pred['alert_message']}")

    print(f"\n{'=' * 65}\n")


if __name__ == "__main__":
    run_local_test()
