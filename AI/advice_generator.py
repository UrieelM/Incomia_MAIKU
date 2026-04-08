"""
Lambda 3: Asesor Financiero IA — Incomia (Equipo HAIKU)
=======================================================
Microservicio que invoca Amazon Bedrock (Claude 3 Opus) para generar
consejos financieros personalizados para trabajadores gig en Mexico 2026.

Arquitectura:
  - Trigger: EventBridge (ForecastReady) o API Gateway POST /api/v1/advice
  - Consume pronostico de liquidez + historial reciente
  - Invoca Bedrock con System Prompt avanzado y empatico
  - Circuit Breaker: si Bedrock falla 3 veces → fallback por 60s

Tolerancia a fallos:
  Circuit Breaker (CLOSED → OPEN → HALF_OPEN)
  Fallback: consejos pre-calculados basados en reglas por sector + risk score

Deploy: AWS Lambda con capa boto3 actualizada.
Dependencias: numpy, boto3
Autor: Equipo HAIKU — Incomia
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

import numpy as np

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.config import Config as BotoConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# ════════════════════════════════════════════════════════════
# LOGGING & CONFIGURACION
# ════════════════════════════════════════════════════════════
logger = logging.getLogger("incomia.ai_advisor")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s | %(message)s"))
    logger.addHandler(_h)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-opus-20240229-v1:0")
BEDROCK_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "1024"))
BEDROCK_TEMPERATURE = float(os.environ.get("BEDROCK_TEMPERATURE", "0.4"))
BEDROCK_TIMEOUT = int(os.environ.get("BEDROCK_TIMEOUT_SECONDS", "8"))
BEDROCK_ANTHROPIC_VERSION = "bedrock-2023-05-31"

DYNAMODB_TABLE_USERS = os.environ.get("DYNAMODB_TABLE_USERS", "incomia_users")
DYNAMODB_TABLE_TRANSACTIONS = os.environ.get("DYNAMODB_TABLE_TRANSACTIONS", "incomia_transactions")
DYNAMODB_TABLE_EXPENSES = os.environ.get("DYNAMODB_TABLE_EXPENSES", "incomia_expenses")
EVENTBRIDGE_BUS = os.environ.get("EVENTBRIDGE_BUS_NAME", "incomia-events")

# Circuit Breaker config
CB_FAILURE_THRESHOLD = int(os.environ.get("CB_FAILURE_THRESHOLD", "3"))
CB_RECOVERY_TIMEOUT = int(os.environ.get("CB_RECOVERY_TIMEOUT_SECONDS", "60"))


# ════════════════════════════════════════════════════════════
# CIRCUIT BREAKER PATTERN
# ════════════════════════════════════════════════════════════

class CircuitBreaker:
    """
    Circuit Breaker para llamadas a Bedrock.
    Estados:
      CLOSED  → normal, llamadas pasan
      OPEN    → bypass, directo a fallback (por CB_RECOVERY_TIMEOUT segundos)
      HALF_OPEN → permite 1 llamada de prueba

    Nota: En Lambda, el estado persiste entre invocaciones calientes
    (mismo container). En invocaciones frias, se reinicia.
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = CB_FAILURE_THRESHOLD,
                 recovery_timeout: int = CB_RECOVERY_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Determina si se puede ejecutar la llamada."""
        if self.state == self.CLOSED:
            return True
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
                logger.info("Circuit Breaker → HALF_OPEN (intentando reconexion)")
                return True
            return False
        if self.state == self.HALF_OPEN:
            return True
        return False

    def record_success(self):
        """Registra exito — resetea el circuit breaker."""
        self.failure_count = 0
        self.state = self.CLOSED
        logger.info("Circuit Breaker → CLOSED (exito)")

    def record_failure(self):
        """Registra fallo — puede abrir el circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning(
                f"Circuit Breaker → OPEN (fallos={self.failure_count}). "
                f"Bypass por {self.recovery_timeout}s."
            )

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout,
        }


# Instancia global (persiste entre invocaciones calientes de Lambda)
_circuit_breaker = CircuitBreaker()


# ════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Asesor Financiero Gig Mexico 2026
# ════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Eres "Incomia AI", un asesor financiero digital especializado en trabajadores de la economia gig en Mexico. Tu mision es ayudarles a estabilizar sus finanzas volatiles y construir resiliencia economica.

## Tu Personalidad
- **Empatico**: Entiendes que los ingresos irregulares generan estres y ansiedad financiera. Nunca juzgas ni usas tono condescendiente. Sabes que un repartidor no elige tener un mal dia de propinas.
- **Practico**: Tus consejos son accionables HOY, no teoricos. Entiendes que estas personas no tienen acceso a productos financieros tradicionales, ni nomina, ni Infonavit.
- **Directo**: Vas al punto. Usas lenguaje sencillo, sin jerga financiera innecesaria. Si usas un termino tecnico, lo explicas en una linea.
- **Motivador**: Reconoces logros pequenos. Un fondo de $500 MXN ya es un avance real.
- **Contextualizado Mexico 2026**: Conoces CETES Directo, Afore voluntaria, tandas, cajas de ahorro comunitarias, y las realidades del costo de vida en Mexico (renta, gasolina, comida, servicios).

## Reglas Estrictas
1. SIEMPRE analiza el contexto financiero antes de aconsejar: ingresos recientes, gastos fijos proximos, saldo del fondo de estabilizacion, y el pronostico de liquidez.
2. SIEMPRE incluye al menos UNA accion concreta que el usuario pueda hacer esta semana.
3. NUNCA recomiendes: criptomonedas, trading, prestamos informales (gota a gota), tarjetas de credito departamentales con tasas abusivas.
4. Si el usuario esta en riesgo de liquidez (risk_score > 70 o prob. quiebra > 60%), PRIORIZA supervivencia financiera: pagar renta, comida, servicios basicos.
5. Adapta tu consejo al sector:
   - GigWorker (Musico): Diversificar fuentes (eventos, clases, streaming), ahorrar de pagos grandes.
   - Delivery (Uber/DiDi): Optimizar horarios de mayor tarifa, control de gasolina, mantenimiento preventivo.
   - Freelance (Plomero): Fidelizar clientes, cobrar anticipo en trabajos grandes, separar material de ganancia.
   - Freelance (Dev): Negociar pagos parciales anticipados, diversificar clientes, retainers mensuales.
6. Responde SIEMPRE en espanol mexicano (sin ser coloquial excesivo).
7. Tu respuesta debe incluir estas secciones:
   - **Tu Panorama**: Resumen de la situacion financiera actual (3-4 lineas).
   - **Consejo Principal**: La accion mas importante ahora mismo (2-3 lineas).
   - **Plan de Accion** (2-3 puntos): Pasos concretos para las proximas 2 semanas.
   - **Meta del Mes**: Un objetivo alcanzable para el mes actual.

## Formato
Responde en texto plano con markdown ligero. Entre 200-350 palabras para que sea digerible en app movil. No uses emojis."""


# ════════════════════════════════════════════════════════════
# CONSTRUCCION DEL PROMPT DE USUARIO
# ════════════════════════════════════════════════════════════

def build_user_prompt(
    user: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    upcoming_expenses: List[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]] = None,
) -> str:
    """Construye el prompt con contexto financiero completo + pronostico."""
    inc_txns = [t for t in recent_transactions if t.get("type") == "ingreso"]
    exp_txns = [t for t in recent_transactions if t.get("type") == "gasto_variable"]
    total_inc = sum(t["amount"] for t in inc_txns)
    total_exp = sum(abs(t["amount"]) for t in exp_txns)
    total_fixed = sum(e["amount"] for e in upcoming_expenses if e.get("is_active", True))
    net = total_inc - total_exp - total_fixed

    # Mejor dia de ingresos
    inc_day: Dict[str, float] = {}
    for t in inc_txns:
        d = t["timestamp"][:10] if isinstance(t["timestamp"], str) else t["timestamp"].strftime("%Y-%m-%d")
        inc_day[d] = inc_day.get(d, 0.0) + t["amount"]
    best_d = max(inc_day, key=inc_day.get) if inc_day else "N/A"
    best_amt = inc_day.get(best_d, 0.0)

    # Fuentes de ingreso
    sources: Dict[str, float] = {}
    for t in inc_txns:
        s = t.get("income_source", "Otros")
        sources[s] = sources.get(s, 0.0) + t["amount"]
    src_text = "\n".join(f"    - {s}: ${a:,.2f} MXN" for s, a in sorted(sources.items(), key=lambda x: -x[1])) or "    - Sin ingresos"

    # Gastos fijos
    exp_text = "\n".join(
        f"    - {e['name']}: ${e['amount']:,.2f} MXN (vence dia {e['due_day_of_month']})"
        for e in upcoming_expenses if e.get("is_active", True)
    ) or "    - Sin gastos fijos"

    # Pronostico
    fc_text = "No disponible."
    if forecast:
        p = forecast.get("prediction", {})
        fc_text = (
            f"- Modelo: {forecast.get('model_used', 'N/A')}\n"
            f"- Prob. quiebra: {p.get('bankruptcy_probability', 0):.1%}\n"
            f"- Risk Score predicho: {p.get('new_risk_score', 'N/A')}/100\n"
            f"- Saldo min. proyectado: ${p.get('min_projected_balance', 0):,.2f} MXN "
            f"(dia {p.get('min_balance_on_day', 'N/A')})\n"
            f"- Alerta: {'SI' if p.get('trigger_liquidity_alert') else 'NO'}"
        )

    today = datetime.utcnow()
    risk = user.get("current_risk_score", 0)
    alert_ctx = ("ALERTA: Score de riesgo ALTO (>70). Priorizar supervivencia financiera."
                 if risk > 70 else "El usuario tiene un riesgo manejable.")

    return f"""Analiza la situacion financiera de este trabajador y dame tu consejo personalizado.

## Perfil del Usuario
- Sector: {user.get('primary_sector', 'N/A')} / {user.get('sub_sector', 'N/A')}
- Display: {user.get('display_name', 'N/A')}
- Salario Artificial: ${user.get('artificial_salary', 0):,.2f} MXN/mes
- Fondo de Estabilizacion: ${user.get('stabilization_fund_balance', 0):,.2f} MXN
- Meta de Resiliencia: {user.get('resilience_goal_type', 'N/A')} (${user.get('resilience_goal_target', 0):,.2f} MXN)
- Score de Riesgo: {risk}/100

## Ultimos 30 Dias
- Ingresos: ${total_inc:,.2f} MXN ({len(inc_txns)} txns)
- Gastos variables: ${total_exp:,.2f} MXN ({len(exp_txns)} txns)
- Gastos fijos mensuales: ${total_fixed:,.2f} MXN
- Balance neto: ${net:,.2f} MXN
- Mejor dia: {best_d} (${best_amt:,.2f} MXN)

## Fuentes de Ingreso
{src_text}

## Gastos Fijos Proximos
{exp_text}

## Pronostico de Liquidez (14 dias)
{fc_text}

## Contexto
- Fecha: {today.strftime('%d de %B de %Y')}
- Economia gig Mexico 2026, ingresos variables.
- {alert_ctx}

Dame tu consejo personalizado siguiendo tu formato estandar."""


# ════════════════════════════════════════════════════════════
# INVOCACION A AMAZON BEDROCK
# ════════════════════════════════════════════════════════════

def invoke_bedrock(
    user: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    upcoming_expenses: List[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Invoca Claude 3 Opus via Bedrock con Circuit Breaker."""
    user_prompt = build_user_prompt(user, recent_transactions, upcoming_expenses, forecast)

    # Verificar circuit breaker
    if not _circuit_breaker.can_execute():
        logger.warning("Circuit Breaker OPEN — usando fallback directo.")
        return {
            "statusCode": 200,
            "advice": _generate_fallback_advice(user, upcoming_expenses, forecast),
            "metadata": {
                "source": "rule_based_fallback",
                "reason": "circuit_breaker_open",
                "circuit_breaker": _circuit_breaker.get_status(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    if not BOTO3_AVAILABLE:
        logger.warning("boto3 no disponible — usando fallback.")
        return {
            "statusCode": 200,
            "advice": _generate_fallback_advice(user, upcoming_expenses, forecast),
            "metadata": {
                "source": "rule_based_fallback",
                "reason": "boto3_unavailable",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    request_body = {
        "anthropic_version": BEDROCK_ANTHROPIC_VERSION,
        "max_tokens": BEDROCK_MAX_TOKENS,
        "temperature": BEDROCK_TEMPERATURE,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    try:
        cfg = BotoConfig(
            region_name=AWS_REGION,
            read_timeout=BEDROCK_TIMEOUT,
            connect_timeout=5,
            retries={"max_attempts": 1, "mode": "standard"},
        )
        client = boto3.client(service_name="bedrock-runtime", config=cfg)
        logger.info(f"Invocando Bedrock modelo={BEDROCK_MODEL_ID} user={user.get('user_id')}")

        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID, contentType="application/json",
            accept="application/json", body=json.dumps(request_body),
        )
        resp_body = json.loads(response["body"].read())
        advice = resp_body["content"][0]["text"]

        _circuit_breaker.record_success()

        return {
            "statusCode": 200,
            "advice": advice,
            "metadata": {
                "source": "bedrock_claude_opus",
                "model_id": BEDROCK_MODEL_ID,
                "user_id": user.get("user_id"),
                "input_tokens": resp_body.get("usage", {}).get("input_tokens"),
                "output_tokens": resp_body.get("usage", {}).get("output_tokens"),
                "circuit_breaker": _circuit_breaker.get_status(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except ClientError as e:
        _circuit_breaker.record_failure()
        logger.error(f"Bedrock ClientError: {e.response['Error']['Message']}")
        return {
            "statusCode": 200,
            "advice": _generate_fallback_advice(user, upcoming_expenses, forecast),
            "metadata": {
                "source": "rule_based_fallback",
                "reason": f"bedrock_error: {e.response['Error']['Message']}",
                "circuit_breaker": _circuit_breaker.get_status(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        _circuit_breaker.record_failure()
        logger.error(f"Error inesperado Bedrock: {e}")
        return {
            "statusCode": 200,
            "advice": _generate_fallback_advice(user, upcoming_expenses, forecast),
            "metadata": {
                "source": "rule_based_fallback",
                "reason": str(e),
                "circuit_breaker": _circuit_breaker.get_status(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }


# ════════════════════════════════════════════════════════════
# CONSEJO FALLBACK (Basado en Reglas)
# ════════════════════════════════════════════════════════════

def _generate_fallback_advice(
    user: Dict[str, Any],
    expenses: List[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]] = None,
) -> str:
    """Consejo basado en reglas cuando Bedrock no esta disponible."""
    risk = user.get("current_risk_score", 50)
    fund = user.get("stabilization_fund_balance", 0)
    salary = user.get("artificial_salary", 0)
    sector = user.get("primary_sector", "General")
    sub = user.get("sub_sector", "")
    total_fixed = sum(e["amount"] for e in expenses if e.get("is_active", True))

    # Incorporar pronostico si disponible
    bp = 0.0
    pred_risk = risk
    if forecast:
        p = forecast.get("prediction", {})
        bp = p.get("bankruptcy_probability", 0)
        pred_risk = p.get("new_risk_score", risk)

    effective_risk = max(risk, pred_risk)

    lines = ["**Tu Panorama**"]
    lines.append(
        f"Tu salario artificial es de ${salary:,.2f} MXN/mes y tienes "
        f"${fund:,.2f} MXN en tu fondo de estabilizacion."
    )
    if bp > 0:
        lines.append(f"El pronostico indica una probabilidad de quiebra del {bp:.0%} en 14 dias.")
    lines.append("")

    # Consejos por sector + riesgo
    sector_tips = {
        "GigWorker": {
            "high": [
                "Busca eventos o tocadas urgentes esta semana, incluso en locales pequenos.",
                "Ofrece clases de musica express a domicilio o en linea.",
                "Cobra anticipos del 50% en tus proximos eventos.",
            ],
            "medium": [
                "Diversifica: ademas de eventos, ofrece clases y contenido en redes.",
                "Ahorra el 20% de cada pago grande de evento inmediatamente.",
                "Investiga CETES Directo para tu fondo (inversion minima $100 MXN).",
            ],
            "low": [
                "Incrementa tu fondo de estabilizacion al 20% de cada ingreso.",
                "Considera Afore voluntaria para ahorro a largo plazo.",
                "Desarrolla un repertorio para eventos corporativos (mejor pagados).",
            ],
        },
        "Delivery": {
            "high": [
                "Activa horas nocturnas viernes y sabado (tarifa dinamica).",
                "Reduce gastos de gasolina optimizando rutas y horarios.",
                "No toques tu fondo de estabilizacion — busca bonos de plataforma.",
            ],
            "medium": [
                "Trabaja en horas pico (12-2pm, 7-10pm) para maximizar ingresos.",
                "Programa mantenimiento preventivo del auto para evitar sorpresas.",
                "Destina el 10% de cada deposito a tu fondo automaticamente.",
            ],
            "low": [
                "Consolida ahorro en CETES o cuenta de rendimiento.",
                "Evalua si conviene cambiar de plataforma o combinar dos.",
                "Meta: fondo de 3 meses de gastos fijos minimos.",
            ],
        },
        "Freelance": {
            "high": [
                "Contacta clientes anteriores para trabajos rapidos esta semana.",
                "Cobra anticipos del 40-50% antes de iniciar cualquier trabajo.",
                "Difiere el pago de servicios no esenciales si es posible.",
            ],
            "medium": [
                "Separa siempre el costo de material de tu ganancia real.",
                "Busca clientes recurrentes para estabilizar ingresos mensuales.",
                "Invierte en herramientas/habilidades que aumenten tu tarifa.",
            ],
            "low": [
                "Negocia retainers mensuales con tus mejores clientes.",
                "Destina 15-20% de cada pago a tu fondo de estabilizacion.",
                "Investiga opciones de inversion segura: CETES, Afore voluntaria.",
            ],
        },
    }

    if effective_risk > 70:
        level = "high"
        lines.append("[ALERTA] Tu riesgo financiero es alto. Prioriza lo esencial.")
        lines.append("")
        lines.append("**Consejo Principal**")
        lines.append(f"Revisa tus gastos fijos (${total_fixed:,.2f} MXN) y negocia plazos para los no urgentes.")
    elif effective_risk > 40:
        level = "medium"
        lines.append("**Consejo Principal**")
        lines.append(
            f"Tu situacion es estable pero mejorable. Destina al menos el 10% "
            f"de cada ingreso (~${salary * 0.10:,.0f} MXN) a tu fondo."
        )
    else:
        level = "low"
        lines.append("**Consejo Principal**")
        lines.append(
            f"Vas por buen camino. Enfocate en llegar a tu meta de "
            f"${user.get('resilience_goal_target', 0):,.2f} MXN."
        )

    tips = sector_tips.get(sector, sector_tips["Freelance"]).get(level, [])
    lines.append("")
    lines.append("**Plan de Accion**")
    for i, tip in enumerate(tips[:3], 1):
        lines.append(f"{i}. {tip}")

    lines.extend([
        "", "**Meta del Mes**",
        f"Aumentar tu fondo de estabilizacion en al menos ${max(salary * 0.05, 200):,.0f} MXN.",
        "", "_Consejo generado automaticamente (modo offline)._",
    ])
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# DYNAMODB — Leer datos
# ════════════════════════════════════════════════════════════

def _decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decimal_to_float(i) for i in obj]
    return obj


def _fetch_user_data(user_id: str):
    """Lee perfil, transacciones y gastos de DynamoDB."""
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 no disponible.")
    cfg = BotoConfig(region_name=AWS_REGION, retries={"max_attempts": 3, "mode": "exponential"})
    ddb = boto3.resource("dynamodb", config=cfg)

    user = _decimal_to_float(ddb.Table(DYNAMODB_TABLE_USERS).get_item(Key={"user_id": user_id}).get("Item", {}))
    if not user:
        raise ValueError(f"Usuario {user_id} no encontrado.")

    txns, exps = [], []
    for tbl_name, lst in [(DYNAMODB_TABLE_TRANSACTIONS, txns), (DYNAMODB_TABLE_EXPENSES, exps)]:
        tbl = ddb.Table(tbl_name)
        kw = {"FilterExpression": "user_id = :uid", "ExpressionAttributeValues": {":uid": user_id}}
        while True:
            r = tbl.scan(**kw)
            lst.extend(_decimal_to_float(r.get("Items", [])))
            if "LastEvaluatedKey" not in r:
                break
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    return user, txns, exps


# ════════════════════════════════════════════════════════════
# LAMBDA HANDLER
# ════════════════════════════════════════════════════════════

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler.
    Triggers:
      1. EventBridge ForecastReady → lee datos de DynamoDB, genera consejo
      2. API Gateway POST → recibe payload directo
      3. Invocacion directa con {user, recent_transactions, upcoming_expenses, forecast}
    """
    logger.info("Lambda ai_advisor invocada.")

    try:
        forecast = None

        # Caso 1: EventBridge ForecastReady
        if event.get("detail-type") == "ForecastReady":
            detail = event.get("detail", {})
            if isinstance(detail, str):
                detail = json.loads(detail)
            user_id = detail.get("user_id")
            if not user_id:
                return {"statusCode": 400, "body": json.dumps({"error": "user_id faltante en evento."})}

            user, txns, exps = _fetch_user_data(user_id)
            # Usar datos del evento como forecast parcial
            forecast = {"prediction": detail, "model_used": detail.get("model_used", "unknown")}

            # Importar liquidity_forecast para pronostico completo si disponible
            try:
                from liquidity_forecast import predict_liquidity
                forecast = predict_liquidity(user, txns, exps)
            except ImportError:
                logger.info("liquidity_forecast no disponible — usando datos del evento.")

            advice_result = invoke_bedrock(user, txns, exps, forecast)
            return {
                "statusCode": advice_result["statusCode"],
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "advice": advice_result["advice"],
                    "prediction": forecast,
                    "metadata": advice_result["metadata"],
                }, default=str, ensure_ascii=False),
            }

        # Caso 2/3: API Gateway o invocacion directa
        body = event
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif isinstance(event.get("body"), dict):
            body = event["body"]

        user = body.get("user", {})
        txns = body.get("recent_transactions", [])
        exps = body.get("upcoming_expenses", [])
        forecast = body.get("forecast")

        # Validar
        required = ["user_id", "primary_sector"]
        missing = [f for f in required if f not in user]
        if missing:
            return {"statusCode": 400, "body": json.dumps({"error": f"Campos faltantes: {missing}"})}

        # Ejecutar pronostico si no viene en el payload
        if not forecast:
            try:
                from liquidity_forecast import predict_liquidity
                forecast = predict_liquidity(user, txns, exps)
            except ImportError:
                logger.info("liquidity_forecast no disponible.")

        advice_result = invoke_bedrock(user, txns, exps, forecast)

        return {
            "statusCode": advice_result["statusCode"],
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "advice": advice_result["advice"],
                "prediction": forecast,
                "metadata": advice_result["metadata"],
            }, default=str, ensure_ascii=False),
        }

    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# ════════════════════════════════════════════════════════════
# EJECUCION LOCAL (Testing)
# ════════════════════════════════════════════════════════════

def run_local_test():
    """Prueba local con datos generados."""
    from data_generator import generate_all_data
    from liquidity_forecast import predict_liquidity

    print("\n" + "=" * 65)
    print("  INCOMIA — Lambda Asesor IA + Prediccion (test local)")
    print("=" * 65)
    print(f"  Modelo Bedrock: {BEDROCK_MODEL_ID}")
    print(f"  Circuit Breaker: {_circuit_breaker.get_status()}")

    data = generate_all_data(num_users=4, days=90)

    for user in data["users"]:
        uid = user["user_id"]
        txns = [t for t in data["transactions"] if t["user_id"] == uid]
        exps = [e for e in data["expenses"] if e["user_id"] == uid]

        print(f"\n{'─' * 65}")
        print(f"  {uid} | {user['display_name']} | {user['primary_sector']}/{user['sub_sector']}")
        print(f"{'─' * 65}")

        # Pronostico
        forecast = predict_liquidity(user, txns, exps)
        p = forecast["prediction"]
        print(f"  Modelo pronostico: {forecast['model_used']}")
        print(f"  Prob. quiebra:     {p['bankruptcy_probability']:.1%}")
        print(f"  Risk Score:        {p['new_risk_score']}/100")
        print(f"  Alerta:            {'SI' if p['trigger_liquidity_alert'] else 'NO'}")
        print(f"  {forecast['alert_message']}")

        # Consejo IA
        print(f"\n  — Consejo IA —")
        advice_result = invoke_bedrock(user, txns, exps, forecast)
        print(f"  Source: {advice_result['metadata'].get('source', 'N/A')}")
        print(f"  CB:     {advice_result['metadata'].get('circuit_breaker', {}).get('state', 'N/A')}")
        print(f"\n{advice_result['advice']}")

    print(f"\n{'=' * 65}\n")


if __name__ == "__main__":
    run_local_test()
