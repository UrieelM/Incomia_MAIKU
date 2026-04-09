"""
Lambda 1: Generador de Datos Sinteticos — Incomia (Equipo HAIKU)
================================================================
Microservicio de simulacion de datos para la economia gig en Mexico 2026.

Arquetipos:
  - Cantante/Musico independiente  → primary_sector: GigWorker
  - Conductor de Uber              → primary_sector: Delivery
  - Plomero a domicilio            → primary_sector: Freelance
  - Desarrollador freelance        → primary_sector: Freelance

Contexto economico: Mexico 2026, inflacion acumulada ~4.2%

Seguridad:
  - PII enmascarado (SHA-256 parcial)
  - Config via variables de entorno
  - Permisos IAM de menor privilegio

Deploy: AWS Lambda. Emite evento DataIngested a EventBridge.
Uso local:
  python data_generator.py                       # genera en consola
  python data_generator.py --output data.json    # guarda JSON
  python data_generator.py --upload              # sube DynamoDB
  python data_generator.py --s3-export           # exporta S3 para Athena

Dependencias: numpy, boto3 (opcional)
Autor: Equipo HAIKU — Incomia
"""

import os
import uuid
import json
import random
import hashlib
import logging
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

import numpy as np

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.config import Config as BotoConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# ════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════
logger = logging.getLogger("incomia.data_generator")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s | %(message)s"))
    logger.addHandler(_h)

# ════════════════════════════════════════════════════════════
# CONFIGURACION VIA VARIABLES DE ENTORNO
# ════════════════════════════════════════════════════════════
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_USERS = os.environ.get("DYNAMODB_TABLE_USERS", "incomia_users")
DYNAMODB_TABLE_TRANSACTIONS = os.environ.get("DYNAMODB_TABLE_TRANSACTIONS", "incomia_transactions")
DYNAMODB_TABLE_EXPENSES = os.environ.get("DYNAMODB_TABLE_EXPENSES", "incomia_expenses")
EVENTBRIDGE_BUS = os.environ.get("EVENTBRIDGE_BUS_NAME", "incomia-events")
EVENTBRIDGE_SRC = os.environ.get("EVENTBRIDGE_SOURCE", "incomia.data-generator")
S3_BUCKET = os.environ.get("S3_BUCKET", "incomia-data-lake")
S3_PREFIX = os.environ.get("S3_PREFIX", "raw/")
DEFAULT_NUM_USERS = int(os.environ.get("DEFAULT_NUM_USERS", "4"))
DEFAULT_DAYS_HISTORY = int(os.environ.get("DEFAULT_DAYS_HISTORY", "90"))
CURRENCY = "MXN"

# ════════════════════════════════════════════════════════════
# CONTEXTO ECONOMICO — MEXICO 2026
# ════════════════════════════════════════════════════════════
MEXICO_2026 = {
    "inflation_factor": 1.042,
    "salario_minimo_diario": 278.80,
    "gasolina_litro": 24.50,
    "tipo_cambio_usd": 18.50,
}

# ════════════════════════════════════════════════════════════
# SEGURIDAD — Enmascaramiento de PII
# ════════════════════════════════════════════════════════════
def mask_email(email: str) -> str:
    """Enmascara email: jo***@gm***.com"""
    if not email or "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    dp = domain.split(".", 1)
    ml = local[:2] + "***" if len(local) > 2 else "***"
    md = dp[0][:2] + "***" if len(dp[0]) > 2 else "***"
    return f"{ml}@{md}.{dp[1] if len(dp) > 1 else '***'}"

def mask_phone(phone: str) -> str:
    """Enmascara telefono: ****5678"""
    return "****" + phone[-4:] if phone and len(phone) >= 4 else "****"

def hash_pii(value: str) -> str:
    """Hash parcial SHA-256 para indexar PII sin exponer datos."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

# ════════════════════════════════════════════════════════════
# PERFILES DE USUARIO — Arquetipos Economia Gig Mexico 2026
# ════════════════════════════════════════════════════════════
def _generate_user_profiles() -> List[Dict[str, Any]]:
    """Genera los 4 perfiles con schema flexible para registro futuro."""
    now = datetime.utcnow().isoformat()
    return [
        {
            "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
            "primary_sector": "GigWorker",
            "sub_sector": "Musico_Independiente",
            "display_name": "Musico Independiente",
            "email_hash": hash_pii("cantante_demo@incomia.mx"),
            "phone_hash": hash_pii("+5255XXXX1234"),
            "artificial_salary": 0.0,
            "stabilization_fund_balance": 800.0,
            "resilience_goal_type": "3 meses de gastos fijos",
            "resilience_goal_target": 27000.0,
            "current_risk_score": 55,
            "created_at": now,
            "profile_version": "2026.1",
            "currency": CURRENCY,
            "city": "CDMX",
        },
        {
            "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
            "primary_sector": "Delivery",
            "sub_sector": "Conductor_Uber",
            "display_name": "Conductor Uber",
            "email_hash": hash_pii("uber_driver@incomia.mx"),
            "phone_hash": hash_pii("+5255XXXX5678"),
            "artificial_salary": 0.0,
            "stabilization_fund_balance": 200.0,
            "resilience_goal_type": "1 mes de gastos fijos",
            "resilience_goal_target": 12000.0,
            "current_risk_score": 70,
            "created_at": now,
            "profile_version": "2026.1",
            "currency": CURRENCY,
            "city": "CDMX",
        },
        {
            "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
            "primary_sector": "Freelance",
            "sub_sector": "Plomero_Domicilio",
            "display_name": "Plomero a Domicilio",
            "email_hash": hash_pii("plomero_demo@incomia.mx"),
            "phone_hash": hash_pii("+5255XXXX9012"),
            "artificial_salary": 0.0,
            "stabilization_fund_balance": 350.0,
            "resilience_goal_type": "2 meses de gastos fijos",
            "resilience_goal_target": 14000.0,
            "current_risk_score": 60,
            "created_at": now,
            "profile_version": "2026.1",
            "currency": CURRENCY,
            "city": "CDMX",
        },
        {
            "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
            "primary_sector": "Freelance",
            "sub_sector": "Desarrollador_Web",
            "display_name": "Desarrollador Freelance",
            "email_hash": hash_pii("dev_freelance@incomia.mx"),
            "phone_hash": hash_pii("+5255XXXX3456"),
            "artificial_salary": 0.0,
            "stabilization_fund_balance": 4500.0,
            "resilience_goal_type": "6 meses de gastos fijos",
            "resilience_goal_target": 72000.0,
            "current_risk_score": 25,
            "created_at": now,
            "profile_version": "2026.1",
            "currency": CURRENCY,
            "city": "CDMX",
        },
    ]

# ════════════════════════════════════════════════════════════
# GASTOS FIJOS — Templates por sub_sector (Mexico 2026)
# ════════════════════════════════════════════════════════════
INF = MEXICO_2026["inflation_factor"]

EXPENSE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "Musico_Independiente": [
        {"name": "Renta",              "amount": round(6500 * INF, 2),  "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",           "amount": round(550 * INF, 2),   "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",                "amount": round(420 * INF, 2),   "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",            "amount": round(350 * INF, 2),   "due_day_of_month": 15, "category": "servicios"},
        {"name": "Mensualidad Equipo", "amount": round(1200 * INF, 2),  "due_day_of_month": 8,  "category": "trabajo"},
        {"name": "Spotify/Apple Music","amount": round(179 * INF, 2),   "due_day_of_month": 12, "category": "trabajo"},
        {"name": "Transporte Eventos", "amount": round(800 * INF, 2),   "due_day_of_month": 20, "category": "transporte"},
    ],
    "Conductor_Uber": [
        {"name": "Renta",              "amount": round(5500 * INF, 2),  "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",           "amount": round(550 * INF, 2),   "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",                "amount": round(400 * INF, 2),   "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",            "amount": round(399 * INF, 2),   "due_day_of_month": 15, "category": "servicios"},
        {"name": "Gasolina",           "amount": round(3200 * INF, 2),  "due_day_of_month": 1,  "category": "transporte"},
        {"name": "Seguro Auto",        "amount": round(1100 * INF, 2),  "due_day_of_month": 20, "category": "transporte"},
        {"name": "Mantenimiento Auto", "amount": round(600 * INF, 2),   "due_day_of_month": 25, "category": "transporte"},
        {"name": "Pago Auto (credito)","amount": round(4500 * INF, 2),  "due_day_of_month": 3,  "category": "transporte"},
    ],
    "Plomero_Domicilio": [
        {"name": "Renta",              "amount": round(4800 * INF, 2),  "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",           "amount": round(450 * INF, 2),   "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",                "amount": round(380 * INF, 2),   "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",            "amount": round(299 * INF, 2),   "due_day_of_month": 15, "category": "servicios"},
        {"name": "Gasolina Moto",      "amount": round(1400 * INF, 2),  "due_day_of_month": 1,  "category": "transporte"},
        {"name": "Material Trabajo",   "amount": round(900 * INF, 2),   "due_day_of_month": 10, "category": "trabajo"},
        {"name": "Herramientas",       "amount": round(350 * INF, 2),   "due_day_of_month": 18, "category": "trabajo"},
    ],
    "Desarrollador_Web": [
        {"name": "Renta",              "amount": round(9500 * INF, 2),  "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet Fibra",     "amount": round(900 * INF, 2),   "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",                "amount": round(550 * INF, 2),   "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",            "amount": round(499 * INF, 2),   "due_day_of_month": 15, "category": "servicios"},
        {"name": "Coworking",          "amount": round(2200 * INF, 2),  "due_day_of_month": 1,  "category": "trabajo"},
        {"name": "GitHub/JetBrains",   "amount": round(450 * INF, 2),   "due_day_of_month": 12, "category": "trabajo"},
        {"name": "Cloud Services",     "amount": round(350 * INF, 2),   "due_day_of_month": 18, "category": "trabajo"},
    ],
}

# ════════════════════════════════════════════════════════════
# GENERADORES DE INGRESO POR ARQUETIPO
# ════════════════════════════════════════════════════════════

def _gen_musician_income(date: datetime, uid: str) -> List[Dict[str, Any]]:
    """Musico: ingresos esporadicos grandes (eventos), bares, clases."""
    txns = []
    dow = date.weekday()
    month = date.month

    # Factor estacional
    sf = 1.0
    if month in [11, 12]: sf = 1.8   # Posadas, fiestas
    elif month in [1, 2]: sf = 0.6   # Enero cuesta arriba
    elif month in [5, 9]: sf = 1.3   # Dia Madres, Fiestas Patrias

    # Evento grande — esporadico viernes-domingo
    if dow in [4, 5, 6] and random.random() < 0.12 * sf:
        amt = random.uniform(3000.0, 15000.0) * INF
        tip = random.uniform(100.0, 800.0) if random.random() < 0.35 else 0.0
        ts = date.replace(hour=random.randint(18, 23), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt + tip, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Evento_Privado",
            "payment_method": random.choice(["Transfer", "Cash"]),
            "description": random.choice([
                "Evento privado (boda)", "Fiesta corporativa",
                "Concierto en bar/foro", "Festival local",
            ]) + (f" + propinas ${tip:.0f}" if tip > 0 else ""),
        })

    # Tocada en bar — jue-sab
    if dow in [3, 4, 5] and random.random() < 0.35 * sf:
        amt = random.uniform(800.0, 2500.0) * INF
        tip = random.uniform(80.0, 400.0) if random.random() < 0.40 else 0.0
        ts = date.replace(hour=random.randint(20, 23), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt + tip, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Bar_Restaurante",
            "payment_method": random.choice(["Cash", "Transfer"]),
            "description": f"Tocada en {'bar' if random.random() < 0.6 else 'restaurante'}"
                           + (f" + propinas ${tip:.0f}" if tip > 0 else ""),
        })

    # Clases de musica — mar-jue
    if dow in [1, 2, 3] and random.random() < 0.30:
        n = random.randint(1, 3)
        amt = n * random.uniform(250.0, 500.0) * INF
        ts = date.replace(hour=random.randint(10, 18), minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Clases_Musica",
            "payment_method": "Transfer",
            "description": f"Clases de musica ({n} alumnos)",
        })
    return txns


def _gen_uber_income(date: datetime, uid: str) -> List[Dict[str, Any]]:
    """Uber: ingresos diarios, picos vie/sab, boost lluvia."""
    txns = []
    dow = date.weekday()
    dom = date.day
    month = date.month

    if random.random() < 0.07:  # Dia libre
        return txns

    if dow in [4, 5]:
        rides, base = random.randint(12, 20), random.uniform(75.0, 150.0)
    elif dow == 6:
        rides, base = random.randint(5, 10), random.uniform(55.0, 100.0)
    else:
        rides, base = random.randint(8, 14), random.uniform(65.0, 120.0)

    rain_prob = 0.25 if month in [6, 7, 8, 9] else 0.08
    rain = 1.30 if random.random() < rain_prob else 1.0
    qna = 1.15 if dom in [14, 15, 16, 29, 30, 31] else 1.0

    total = rides * base * rain * qna * random.uniform(0.85, 1.15) * INF
    tip = random.uniform(30.0, 120.0) if random.random() < 0.25 else 0.0

    plat = random.choice(["Uber", "DiDi", "InDriver"])
    ts = date.replace(hour=random.randint(6, 23), minute=random.randint(0, 59), second=0)
    desc = f"{rides} viajes completados"
    if rain > 1.0: desc += " (tarifa dinamica por lluvia)"
    if tip > 0: desc += f" + propinas ${tip:.0f}"

    txns.append({
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "user_id": uid, "timestamp": ts.isoformat(),
        "amount": round(total + tip, 2), "currency": CURRENCY,
        "type": "ingreso", "income_source": plat,
        "payment_method": "Transfer", "description": desc,
    })
    return txns


def _gen_plumber_income(date: datetime, uid: str) -> List[Dict[str, Any]]:
    """Plomero: ingresos diarios pequenos, 1-3 servicios, trabajos grandes esporadicos."""
    txns = []
    dow = date.weekday()

    if dow == 6 and random.random() < 0.60:
        return txns
    if random.random() < 0.10:
        return txns

    n_srv = random.randint(2, 4) if dow in [5, 6] else random.randint(1, 3)
    servicios = [
        "Reparacion de fuga", "Destape de caneria", "Instalacion de llave",
        "Reparacion de WC", "Cambio de tuberia", "Instalacion de calentador",
        "Mantenimiento preventivo", "Reparacion de tinaco",
    ]
    for _ in range(n_srv):
        amt = random.uniform(300.0, 900.0) * INF
        ts = date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Servicio_Domicilio",
            "payment_method": random.choice(["Cash", "Transfer"]),
            "description": random.choice(servicios),
        })

    # Trabajo grande esporadico
    if random.random() < 0.06:
        amt = random.uniform(1500.0, 4500.0) * INF
        ts = date.replace(hour=10, minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Proyecto_Grande",
            "payment_method": "Transfer",
            "description": random.choice([
                "Remodelacion de bano completo",
                "Instalacion de red hidraulica",
                "Proyecto de plomeria integral",
            ]),
        })
    return txns


def _gen_dev_income(date: datetime, uid: str) -> List[Dict[str, Any]]:
    """Dev Freelance: pagos por hitos mitad/fin mes, semanales viernes."""
    txns = []
    dow = date.weekday()
    dom = date.day

    # Milestone mitad de mes
    if dom in [14, 15, 16] and random.random() < 0.60:
        amt = random.uniform(10000.0, 22000.0) * INF
        plat = random.choice(["Upwork", "Toptal", "Cliente_Directo"])
        ts = date.replace(hour=10, minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": plat,
            "payment_method": "Transfer",
            "description": f"Pago milestone proyecto — {plat}",
        })

    # Pago final fin de mes
    if dom in [28, 29, 30, 31] and random.random() < 0.65:
        amt = random.uniform(12000.0, 30000.0) * INF
        ts = date.replace(hour=14, minute=30, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Cliente_Directo",
            "payment_method": "Transfer",
            "description": "Pago final de proyecto — cliente directo",
        })

    # Pago semanal viernes
    if dow == 4 and random.random() < 0.75:
        hrs = random.randint(12, 35)
        rate = random.uniform(350.0, 650.0)
        amt = hrs * rate * INF
        ts = date.replace(hour=18, minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(amt, 2), "currency": CURRENCY,
            "type": "ingreso", "income_source": "Freelance_Platform",
            "payment_method": "Transfer",
            "description": f"Pago semanal ({hrs}h x ${rate:.0f}/h)",
        })
    return txns


INCOME_GENERATORS = {
    "Musico_Independiente": _gen_musician_income,
    "Conductor_Uber": _gen_uber_income,
    "Plomero_Domicilio": _gen_plumber_income,
    "Desarrollador_Web": _gen_dev_income,
}

# ════════════════════════════════════════════════════════════
# GASTOS VARIABLES (Mexico 2026)
# ════════════════════════════════════════════════════════════

def _gen_var_expenses(date: datetime, uid: str, sub: str) -> List[Dict[str, Any]]:
    """Gastos variables diarios realistas."""
    txns = []

    # Comida (70%)
    if random.random() < 0.70:
        amt = random.uniform(60.0, 380.0) * INF
        ts = date.replace(hour=random.randint(7, 21), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": random.choice(["Debit_Card", "Cash", "E-Wallet"]),
            "description": random.choice([
                "Desayuno/comida en fonda", "Compra en tienda/OXXO",
                "Cena fuera", "Despensa semanal parcial",
            ]),
        })

    # Transporte (40%)
    if random.random() < 0.40:
        amt = random.uniform(25.0, 200.0) * INF
        ts = date.replace(hour=random.randint(6, 22), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": random.choice(["Cash", "E-Wallet"]),
            "description": random.choice(["Metro/Metrobus", "Uber personal", "Gasolina adicional"]),
        })

    # Entretenimiento (25%)
    if random.random() < 0.25:
        amt = random.uniform(50.0, 450.0) * INF
        ts = date.replace(hour=random.randint(14, 23), minute=random.randint(0, 59), second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": random.choice(["Debit_Card", "E-Wallet"]),
            "description": random.choice([
                "Cafe/snack", "Streaming", "Salida con amigos", "Farmacia/salud",
            ]),
        })

    # Gastos especificos por sector
    if sub == "Conductor_Uber" and random.random() < 0.30:
        amt = random.uniform(50.0, 180.0) * INF
        ts = date.replace(hour=random.randint(7, 20), minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": "Cash",
            "description": random.choice(["Lavado de auto", "Cafe/agua en ruta", "Caseta"]),
        })
    elif sub == "Plomero_Domicilio" and random.random() < 0.35:
        amt = random.uniform(100.0, 600.0) * INF
        ts = date.replace(hour=random.randint(7, 12), minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": "Cash",
            "description": random.choice([
                "Material (tuberias/conexiones)", "Sellador/pegamento", "Herramienta repuesto",
            ]),
        })
    elif sub == "Musico_Independiente" and random.random() < 0.15:
        amt = random.uniform(80.0, 400.0) * INF
        ts = date.replace(hour=random.randint(10, 18), minute=0, second=0)
        txns.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": uid, "timestamp": ts.isoformat(),
            "amount": round(-amt, 2), "currency": CURRENCY,
            "type": "gasto_variable", "income_source": "",
            "payment_method": random.choice(["Cash", "Debit_Card"]),
            "description": random.choice(["Cuerdas/baquetas", "Renta equipo sonido", "Partituras"]),
        })
    return txns

# ════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES DE GENERACION
# ════════════════════════════════════════════════════════════

def generate_expenses_for_user(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Genera gastos fijos mensuales del usuario."""
    uid = user["user_id"]
    sub = user.get("sub_sector", "Conductor_Uber")
    tmpls = EXPENSE_TEMPLATES.get(sub, EXPENSE_TEMPLATES["Conductor_Uber"])
    return [{
        "expense_id": f"EXP-{uuid.uuid4().hex[:8].upper()}",
        "user_id": uid, "name": t["name"], "amount": t["amount"],
        "due_day_of_month": t["due_day_of_month"], "category": t["category"],
        "is_active": True, "currency": CURRENCY,
        "created_at": datetime.utcnow().isoformat(),
    } for t in tmpls]


def generate_transactions_for_user(user: Dict[str, Any], days: int = DEFAULT_DAYS_HISTORY) -> List[Dict[str, Any]]:
    """Genera historial de transacciones (ingresos + gastos variables)."""
    uid = user["user_id"]
    sub = user.get("sub_sector", "Conductor_Uber")
    gen = INCOME_GENERATORS.get(sub, _gen_uber_income)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cur = today - timedelta(days=days)
    all_txns: List[Dict[str, Any]] = []
    while cur <= today:
        all_txns.extend(gen(cur, uid))
        all_txns.extend(_gen_var_expenses(cur, uid, sub))
        cur += timedelta(days=1)
    all_txns.sort(key=lambda t: t["timestamp"])
    return all_txns


def calculate_artificial_salary(transactions: List[Dict[str, Any]]) -> float:
    """Salario artificial: mediana de ingresos mensuales."""
    inc = [t for t in transactions if t.get("type") == "ingreso"]
    if not inc:
        return 0.0
    monthly: Dict[str, float] = {}
    for t in inc:
        k = t["timestamp"][:7]
        monthly[k] = monthly.get(k, 0.0) + t["amount"]
    return round(float(np.median(list(monthly.values()))), 2) if monthly else 0.0


def generate_all_data(num_users: int = DEFAULT_NUM_USERS, days: int = DEFAULT_DAYS_HISTORY) -> Dict[str, Any]:
    """Genera dataset completo: usuarios, transacciones y gastos."""
    users, all_txns, all_exp = [], [], []
    profiles = _generate_user_profiles()[:num_users]
    for u in profiles:
        txns = generate_transactions_for_user(u, days)
        all_txns.extend(txns)
        u["artificial_salary"] = calculate_artificial_salary(txns)
        users.append(u)
        all_exp.extend(generate_expenses_for_user(u))
    logger.info(f"Generados: {len(users)} usuarios, {len(all_txns)} txns, {len(all_exp)} gastos fijos.")
    return {
        "users": users, "transactions": all_txns, "expenses": all_exp,
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "generator_version": "2026.1.0", "context": "Mexico_2026",
            "inflation_factor": INF, "days_history": days,
        },
    }

# ════════════════════════════════════════════════════════════
# CARGA A DYNAMODB (retry exponencial)
# ════════════════════════════════════════════════════════════

def _to_decimal(item: Any) -> Any:
    """Convierte float → Decimal recursivamente para DynamoDB."""
    if isinstance(item, float):
        return Decimal(str(item))
    elif isinstance(item, dict):
        return {k: _to_decimal(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [_to_decimal(i) for i in item]
    return item


def upload_to_dynamodb(data: Dict[str, Any]) -> Dict[str, int]:
    """Sube datos a DynamoDB con batch_writer y retry exponencial."""
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 no disponible.")
    cfg = BotoConfig(region_name=AWS_REGION, retries={"max_attempts": 3, "mode": "exponential"})
    ddb = boto3.resource("dynamodb", config=cfg)
    counts = {}
    mapping = [
        ("users", DYNAMODB_TABLE_USERS),
        ("transactions", DYNAMODB_TABLE_TRANSACTIONS),
        ("expenses", DYNAMODB_TABLE_EXPENSES),
    ]
    for key, table_name in mapping:
        tbl = ddb.Table(table_name)
        logger.info(f"Subiendo {len(data[key])} {key} a {table_name}...")
        with tbl.batch_writer() as batch:
            for item in data[key]:
                batch.put_item(Item=_to_decimal(item))
        counts[key] = len(data[key])
    logger.info(f"Carga DynamoDB completa: {counts}")
    return counts

# ════════════════════════════════════════════════════════════
# EXPORTACION A S3 (JSON-Lines para Athena)
# ════════════════════════════════════════════════════════════

def export_to_s3(data: Dict[str, Any], bucket: Optional[str] = None) -> Dict[str, str]:
    """Exporta en JSON-Lines particionado por fecha para Athena."""
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 no disponible.")
    bucket = bucket or S3_BUCKET
    s3 = boto3.client("s3", region_name=AWS_REGION)
    now = datetime.utcnow()
    part = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    uploaded = {}
    for tbl, records in [("users", data["users"]), ("transactions", data["transactions"]), ("expenses", data["expenses"])]:
        key = f"{S3_PREFIX}{tbl}/{part}/data.jsonl"
        body = "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in records)
        try:
            s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"),
                          ContentType="application/x-ndjson", ServerSideEncryption="AES256")
            uploaded[tbl] = f"s3://{bucket}/{key}"
            logger.info(f"[S3] {tbl}: {len(records)} → s3://{bucket}/{key}")
        except ClientError as e:
            logger.error(f"[S3] Error {tbl}: {e}")
            raise
    return uploaded

# ════════════════════════════════════════════════════════════
# EVENTBRIDGE — Emitir DataIngested
# ════════════════════════════════════════════════════════════

def emit_event(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Emite evento DataIngested a EventBridge."""
    if not BOTO3_AVAILABLE:
        logger.warning("boto3 no disponible — evento no emitido.")
        return None
    try:
        eb = boto3.client("events", region_name=AWS_REGION)
        detail = {
            "event_type": "DataIngested",
            "user_ids": [u["user_id"] for u in data["users"]],
            "transaction_count": len(data["transactions"]),
            "timestamp": datetime.utcnow().isoformat(),
        }
        resp = eb.put_events(Entries=[{
            "Source": EVENTBRIDGE_SRC, "DetailType": "DataIngested",
            "Detail": json.dumps(detail), "EventBusName": EVENTBRIDGE_BUS,
        }])
        logger.info(f"Evento DataIngested emitido: {detail['user_ids']}")
        return resp
    except Exception as e:
        logger.error(f"Error EventBridge: {e}")
        return None

# ════════════════════════════════════════════════════════════
# LAMBDA HANDLER
# ════════════════════════════════════════════════════════════

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler. Genera datos y los inyecta a DynamoDB/S3."""
    logger.info("Lambda data_generator invocada.")
    try:
        body = event
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif isinstance(event.get("body"), dict):
            body = event["body"]

        num_users = body.get("num_users", DEFAULT_NUM_USERS)
        days = body.get("days_history", DEFAULT_DAYS_HISTORY)
        seed = body.get("seed")
        if seed is not None:
            random.seed(seed); np.random.seed(seed)

        data = generate_all_data(num_users=num_users, days=days)
        result = {
            "users_generated": len(data["users"]),
            "transactions_generated": len(data["transactions"]),
            "expenses_generated": len(data["expenses"]),
            "user_ids": [u["user_id"] for u in data["users"]],
        }

        if body.get("upload_dynamodb", True):
            try:
                result["dynamodb"] = {"status": "success", "counts": upload_to_dynamodb(data)}
            except Exception as e:
                result["dynamodb"] = {"status": "error", "message": str(e)}

        if body.get("export_s3", True):
            try:
                result["s3"] = {"status": "success", "paths": export_to_s3(data)}
            except Exception as e:
                result["s3"] = {"status": "error", "message": str(e)}

        if body.get("emit_event", True):
            emit_event(data)
            result["eventbridge"] = "emitted"

        return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result, default=str, ensure_ascii=False)}
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# ════════════════════════════════════════════════════════════
# CLI & RESUMEN
# ════════════════════════════════════════════════════════════

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def print_summary(data: Dict[str, Any]) -> None:
    """Imprime resumen legible."""
    print("\n" + "=" * 65)
    print("  INCOMIA — Datos Sinteticos (Mexico 2026)")
    print("=" * 65)
    m = data.get("metadata", {})
    print(f"  Generado:      {m.get('generated_at', 'N/A')}")
    print(f"  Version:       {m.get('generator_version', 'N/A')}")
    print(f"  Inflacion:     {m.get('inflation_factor', 'N/A')}x")
    print(f"  Historial:     {m.get('days_history', 'N/A')} dias")
    print(f"\n  Usuarios:      {len(data['users'])}")
    print(f"  Transacciones: {len(data['transactions'])}")
    print(f"  Gastos fijos:  {len(data['expenses'])}")
    print("\n  — Detalle por usuario —")
    for u in data["users"]:
        uid = u["user_id"]
        ut = [t for t in data["transactions"] if t["user_id"] == uid]
        inc = sum(t["amount"] for t in ut if t["type"] == "ingreso")
        exp = sum(abs(t["amount"]) for t in ut if t["type"] == "gasto_variable")
        print(f"\n  [{uid}] {u['display_name']} ({u['primary_sector']}/{u['sub_sector']})")
        print(f"    Salario Artificial:   ${u['artificial_salary']:,.2f} MXN")
        print(f"    Fondo Estabilizacion: ${u['stabilization_fund_balance']:,.2f} MXN")
        print(f"    Risk Score:           {u['current_risk_score']}/100")
        print(f"    Ingresos totales:     ${inc:,.2f} MXN")
        print(f"    Gastos variables:     ${exp:,.2f} MXN")
    print("\n" + "=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Incomia — Simulador Economia Gig Mexico 2026")
    parser.add_argument("--users", type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS_HISTORY)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--upload", action="store_true", help="Subir a DynamoDB")
    parser.add_argument("--s3-export", action="store_true", help="Exportar a S3")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed); np.random.seed(args.seed)

    print("\nGenerando datos sinteticos para Incomia...")
    data = generate_all_data(num_users=args.users, days=args.days)
    print_summary(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        print(f"\nDatos guardados en: {args.output}")

    if args.upload:
        upload_to_dynamodb(data)
    if args.s3_export:
        export_to_s3(data)

    print("\nMuestra (primeras 3 transacciones):")
    for t in data["transactions"][:3]:
        print(json.dumps(t, indent=2, ensure_ascii=False))
    return data


if __name__ == "__main__":
    main()
