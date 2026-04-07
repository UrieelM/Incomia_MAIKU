"""
Script generador de datos sinteticos para la economia gig.
Autocontenido: no depende de archivos externos (config.py).

Genera datos realistas que replican los patrones:
  - Picos de ingresos Uber/Rappi los fines de semana.
  - Pagos de Upwork/Freelancer a mitad y fin de mes.
  - Gastos fijos recurrentes (renta, internet, servicios).
  - Variabilidad estocastica para emular la vida real.

Uso:
  python entregable_1_generador_datos.py                       # genera datos en consola
  python entregable_1_generador_datos.py --output data.json    # guarda en archivo JSON
  python entregable_1_generador_datos.py --upload              # genera y sube a DynamoDB
  python entregable_1_generador_datos.py --s3-bucket mi-bucket  # sube a S3
  python entregable_1_generador_datos.py --users 5 --seed 42   # reproducible, 5 usuarios

Dependencias: numpy, boto3 (opcional, solo para --upload/--s3-bucket)
Autor: Equipo Incomia
"""

import uuid
import json
import random
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


# ════════════════════════════════════════════════════════════
# CONFIGURACION (inlined de config.py)
# ════════════════════════════════════════════════════════════

AWS_REGION = "us-east-1"

DYNAMODB_TABLE_USERS = "incomia_users"
DYNAMODB_TABLE_TRANSACTIONS = "incomia_transactions"
DYNAMODB_TABLE_EXPENSES = "incomia_expenses"

DEFAULT_NUM_USERS = 20
DEFAULT_DAYS_HISTORY = 90           # 3 meses de historial
CURRENCY_DEFAULT = "MXN"

S3_BUCKET_DEFAULT = "incomia-data"
S3_PREFIX = "incomia_data/"


# ════════════════════════════════════════════════════════════
# PERFILES DE USUARIO — Arquetipos de la economia gig
# ════════════════════════════════════════════════════════════

USER_PROFILES = [
    # ── Delivery (6 usuarios) ─────────────────────────────────
    {
        "user_id": "USR-1001", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 500.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 22500.0, "current_risk_score": 45,
    },
    {
        "user_id": "USR-1004", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 0.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 18000.0, "current_risk_score": 88,
    },
    {
        "user_id": "USR-1006", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 2100.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 21000.0, "current_risk_score": 38,
    },
    {
        "user_id": "USR-1010", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 50.0,
        "resilience_goal_type": "1 mes de gastos fijos",
        "resilience_goal_target": 7500.0, "current_risk_score": 92,
    },
    {
        "user_id": "USR-1014", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 4200.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 22500.0, "current_risk_score": 25,
    },
    {
        "user_id": "USR-1018", "primary_sector": "Delivery",
        "artificial_salary": 0.0, "stabilization_fund_balance": 800.0,
        "resilience_goal_type": "1 mes de gastos fijos",
        "resilience_goal_target": 7500.0, "current_risk_score": 60,
    },

    # ── Freelance Dev (5 usuarios) ────────────────────────────
    {
        "user_id": "USR-1002", "primary_sector": "Freelance_Dev",
        "artificial_salary": 0.0, "stabilization_fund_balance": 3200.0,
        "resilience_goal_type": "6 meses de gastos fijos",
        "resilience_goal_target": 54000.0, "current_risk_score": 30,
    },
    {
        "user_id": "USR-1007", "primary_sector": "Freelance_Dev",
        "artificial_salary": 0.0, "stabilization_fund_balance": 15000.0,
        "resilience_goal_type": "6 meses de gastos fijos",
        "resilience_goal_target": 66000.0, "current_risk_score": 12,
    },
    {
        "user_id": "USR-1011", "primary_sector": "Freelance_Dev",
        "artificial_salary": 0.0, "stabilization_fund_balance": 0.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 33000.0, "current_risk_score": 75,
    },
    {
        "user_id": "USR-1015", "primary_sector": "Freelance_Dev",
        "artificial_salary": 0.0, "stabilization_fund_balance": 8400.0,
        "resilience_goal_type": "6 meses de gastos fijos",
        "resilience_goal_target": 54000.0, "current_risk_score": 22,
    },
    {
        "user_id": "USR-1019", "primary_sector": "Freelance_Dev",
        "artificial_salary": 0.0, "stabilization_fund_balance": 1200.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 33000.0, "current_risk_score": 55,
    },

    # ── Rideshare (5 usuarios) ────────────────────────────────
    {
        "user_id": "USR-1003", "primary_sector": "Rideshare",
        "artificial_salary": 0.0, "stabilization_fund_balance": 150.0,
        "resilience_goal_type": "1 mes de gastos fijos",
        "resilience_goal_target": 8000.0, "current_risk_score": 72,
    },
    {
        "user_id": "USR-1008", "primary_sector": "Rideshare",
        "artificial_salary": 0.0, "stabilization_fund_balance": 5600.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 27600.0, "current_risk_score": 28,
    },
    {
        "user_id": "USR-1012", "primary_sector": "Rideshare",
        "artificial_salary": 0.0, "stabilization_fund_balance": 0.0,
        "resilience_goal_type": "1 mes de gastos fijos",
        "resilience_goal_target": 9200.0, "current_risk_score": 85,
    },
    {
        "user_id": "USR-1016", "primary_sector": "Rideshare",
        "artificial_salary": 0.0, "stabilization_fund_balance": 3000.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 27600.0, "current_risk_score": 40,
    },
    {
        "user_id": "USR-1020", "primary_sector": "Rideshare",
        "artificial_salary": 0.0, "stabilization_fund_balance": 900.0,
        "resilience_goal_type": "1 mes de gastos fijos",
        "resilience_goal_target": 9200.0, "current_risk_score": 65,
    },

    # ── Freelance Design (4 usuarios) ─────────────────────────
    {
        "user_id": "USR-1005", "primary_sector": "Freelance_Design",
        "artificial_salary": 0.0, "stabilization_fund_balance": 8500.0,
        "resilience_goal_type": "6 meses de gastos fijos",
        "resilience_goal_target": 60000.0, "current_risk_score": 15,
    },
    {
        "user_id": "USR-1009", "primary_sector": "Freelance_Design",
        "artificial_salary": 0.0, "stabilization_fund_balance": 200.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 28500.0, "current_risk_score": 78,
    },
    {
        "user_id": "USR-1013", "primary_sector": "Freelance_Design",
        "artificial_salary": 0.0, "stabilization_fund_balance": 12000.0,
        "resilience_goal_type": "6 meses de gastos fijos",
        "resilience_goal_target": 57000.0, "current_risk_score": 18,
    },
    {
        "user_id": "USR-1017", "primary_sector": "Freelance_Design",
        "artificial_salary": 0.0, "stabilization_fund_balance": 1500.0,
        "resilience_goal_type": "3 meses de gastos fijos",
        "resilience_goal_target": 28500.0, "current_risk_score": 52,
    },
]


# ════════════════════════════════════════════════════════════
# GASTOS FIJOS — Templates por perfil
# ════════════════════════════════════════════════════════════

EXPENSE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "Delivery": [
        {"name": "Renta",       "amount": 4500.0, "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",    "amount": 450.0,  "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",         "amount": 350.0,  "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",     "amount": 299.0,  "due_day_of_month": 15, "category": "servicios"},
        {"name": "Gasolina",    "amount": 1200.0, "due_day_of_month": 1,  "category": "transporte"},
        {"name": "Seguro Moto", "amount": 350.0,  "due_day_of_month": 20, "category": "transporte"},
    ],
    "Freelance_Dev": [
        {"name": "Renta",       "amount": 7500.0,  "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",    "amount": 800.0,   "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",         "amount": 500.0,   "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",     "amount": 499.0,   "due_day_of_month": 15, "category": "servicios"},
        {"name": "Coworking",   "amount": 1500.0,  "due_day_of_month": 1,  "category": "trabajo"},
        {"name": "GitHub Pro",  "amount": 200.0,   "due_day_of_month": 12, "category": "trabajo"},
    ],
    "Rideshare": [
        {"name": "Renta",        "amount": 5000.0, "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",     "amount": 450.0,  "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",          "amount": 400.0,  "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",      "amount": 349.0,  "due_day_of_month": 15, "category": "servicios"},
        {"name": "Gasolina",     "amount": 2000.0, "due_day_of_month": 1,  "category": "transporte"},
        {"name": "Seguro Auto",  "amount": 900.0,  "due_day_of_month": 20, "category": "transporte"},
        {"name": "Mantenimiento","amount": 500.0,  "due_day_of_month": 25, "category": "transporte"},
    ],
    "Freelance_Design": [
        {"name": "Renta",        "amount": 6500.0, "due_day_of_month": 1,  "category": "vivienda"},
        {"name": "Internet",     "amount": 700.0,  "due_day_of_month": 5,  "category": "servicios"},
        {"name": "Luz",          "amount": 450.0,  "due_day_of_month": 10, "category": "servicios"},
        {"name": "Celular",      "amount": 399.0,  "due_day_of_month": 15, "category": "servicios"},
        {"name": "Adobe CC",     "amount": 1100.0, "due_day_of_month": 8,  "category": "trabajo"},
        {"name": "Figma Pro",    "amount": 250.0,  "due_day_of_month": 8,  "category": "trabajo"},
    ],
}


# ════════════════════════════════════════════════════════════
# PATRONES DE INGRESO — Logica estacional por sector
# ════════════════════════════════════════════════════════════

def _generate_delivery_income(date: datetime, user_id: str) -> List[Dict[str, Any]]:
    """Patron Delivery (Uber Eats, Rappi, DiDi Food):
    Fines de semana = picos altos. Quincenas = mas pedidos."""
    transactions = []
    day_of_week = date.weekday()
    day_of_month = date.day
    is_weekend = day_of_week >= 4
    is_quincena = day_of_month in [14, 15, 16, 29, 30, 31]

    if is_weekend:
        num_deliveries = random.randint(8, 15)
        base_per_delivery = random.uniform(55.0, 95.0)
    else:
        num_deliveries = random.randint(3, 8)
        base_per_delivery = random.uniform(40.0, 70.0)

    quincena_multiplier = 1.3 if is_quincena else 1.0

    if random.random() < 0.10:
        return transactions

    total_day_income = num_deliveries * base_per_delivery * quincena_multiplier
    total_day_income *= random.uniform(0.85, 1.15)

    platforms = ["Uber_Eats", "Rappi", "DiDi_Food"]
    chosen_platform = random.choice(platforms)

    tip_amount = 0.0
    if random.random() < 0.20:
        tip_amount = random.uniform(20.0, 80.0)

    hour = random.randint(11, 22)
    minute = random.randint(0, 59)
    ts = date.replace(hour=hour, minute=minute, second=0)

    transactions.append({
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "user_id": user_id,
        "timestamp": ts.isoformat(),
        "amount": round(total_day_income + tip_amount, 2),
        "currency": CURRENCY_DEFAULT,
        "type": "ingreso",
        "income_source": chosen_platform,
        "payment_method": "E-Wallet",
        "description": f"Entregas del dia ({num_deliveries} pedidos) + propinas" if tip_amount > 0
                        else f"Entregas del dia ({num_deliveries} pedidos)",
    })
    return transactions


def _generate_rideshare_income(date: datetime, user_id: str) -> List[Dict[str, Any]]:
    """Patron Rideshare (Uber, DiDi, InDriver):
    Viernes/sabado = premium. Lluvia = boost."""
    transactions = []
    day_of_week = date.weekday()

    if random.random() < 0.08:
        return transactions

    if day_of_week in [4, 5]:
        num_rides = random.randint(10, 18)
        base_per_ride = random.uniform(70.0, 140.0)
    elif day_of_week == 6:
        num_rides = random.randint(4, 9)
        base_per_ride = random.uniform(50.0, 90.0)
    else:
        num_rides = random.randint(6, 12)
        base_per_ride = random.uniform(55.0, 100.0)

    rain_boost = 1.25 if random.random() < 0.15 else 1.0
    total_income = num_rides * base_per_ride * rain_boost
    total_income *= random.uniform(0.85, 1.15)

    platforms = ["Uber", "DiDi", "InDriver"]
    chosen_platform = random.choice(platforms)
    hour = random.randint(6, 23)
    minute = random.randint(0, 59)
    ts = date.replace(hour=hour, minute=minute, second=0)

    description = f"{num_rides} viajes completados"
    if rain_boost > 1.0:
        description += " (tarifa dinamica por lluvia)"

    transactions.append({
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "user_id": user_id,
        "timestamp": ts.isoformat(),
        "amount": round(total_income, 2),
        "currency": CURRENCY_DEFAULT,
        "type": "ingreso",
        "income_source": chosen_platform,
        "payment_method": "Transfer",
        "description": description,
    })
    return transactions


def _generate_freelance_dev_income(date: datetime, user_id: str) -> List[Dict[str, Any]]:
    """Patron Freelance Dev (Upwork, Toptal):
    Pagos grandes a mitad/fin de mes. Pagos semanales los viernes."""
    transactions = []
    day_of_week = date.weekday()
    day_of_month = date.day

    if day_of_month in [14, 15, 16]:
        if random.random() < 0.65:
            amount = random.uniform(8000.0, 18000.0)
            platform = random.choice(["Upwork", "Toptal"])
            ts = date.replace(hour=10, minute=0, second=0)
            transactions.append({
                "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id, "timestamp": ts.isoformat(),
                "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
                "type": "ingreso", "income_source": "Freelance_Platform",
                "payment_method": "Transfer",
                "description": f"Pago milestone proyecto -- {platform}",
            })

    if day_of_month in [28, 29, 30, 31]:
        if random.random() < 0.70:
            amount = random.uniform(10000.0, 25000.0)
            ts = date.replace(hour=14, minute=30, second=0)
            transactions.append({
                "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id, "timestamp": ts.isoformat(),
                "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
                "type": "ingreso", "income_source": "Direct_Client",
                "payment_method": "Transfer",
                "description": "Pago final de proyecto -- cliente directo",
            })

    if day_of_week == 4:
        if random.random() < 0.80:
            hours = random.randint(10, 30)
            rate = random.uniform(250.0, 500.0)
            amount = hours * rate
            ts = date.replace(hour=18, minute=0, second=0)
            transactions.append({
                "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id, "timestamp": ts.isoformat(),
                "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
                "type": "ingreso", "income_source": "Freelance_Platform",
                "payment_method": "Transfer",
                "description": f"Pago semanal ({hours}h x ${rate:.0f}/h)",
            })
    return transactions


def _generate_freelance_design_income(date: datetime, user_id: str) -> List[Dict[str, Any]]:
    """Patron Freelance Design (Fiverr, 99designs):
    Proyectos irregulares con entregas parciales."""
    transactions = []
    day_of_month = date.day
    day_of_week = date.weekday()

    if day_of_month in [10, 11, 12]:
        if random.random() < 0.55:
            amount = random.uniform(6000.0, 15000.0)
            ts = date.replace(hour=12, minute=0, second=0)
            transactions.append({
                "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id, "timestamp": ts.isoformat(),
                "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
                "type": "ingreso", "income_source": "Direct_Client",
                "payment_method": "Transfer",
                "description": "Entrega de branding/diseno -- cliente directo",
            })

    if day_of_month in [22, 23, 24, 25]:
        if random.random() < 0.60:
            amount = random.uniform(5000.0, 12000.0)
            ts = date.replace(hour=16, minute=0, second=0)
            transactions.append({
                "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id, "timestamp": ts.isoformat(),
                "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
                "type": "ingreso", "income_source": "Freelance_Platform",
                "payment_method": "E-Wallet",
                "description": "Pago proyecto UI/UX -- Fiverr/99designs",
            })

    if day_of_week in [1, 3] and random.random() < 0.35:
        amount = random.uniform(500.0, 2500.0)
        ts = date.replace(hour=random.randint(9, 19), minute=random.randint(0, 59), second=0)
        transactions.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id, "timestamp": ts.isoformat(),
            "amount": round(amount, 2), "currency": CURRENCY_DEFAULT,
            "type": "ingreso", "income_source": "Freelance_Platform",
            "payment_method": "E-Wallet",
            "description": "Revision de diseno / ajustes menores",
        })
    return transactions


INCOME_GENERATORS = {
    "Delivery": _generate_delivery_income,
    "Freelance_Dev": _generate_freelance_dev_income,
    "Rideshare": _generate_rideshare_income,
    "Freelance_Design": _generate_freelance_design_income,
}


# ════════════════════════════════════════════════════════════
# GENERADOR DE GASTOS VARIABLES
# ════════════════════════════════════════════════════════════

def _generate_variable_expenses(date: datetime, user_id: str) -> List[Dict[str, Any]]:
    """Genera gastos variables diarios: comida, transporte, entretenimiento."""
    transactions = []
    if random.random() < 0.70:
        amount = random.uniform(50.0, 350.0)
        categories = [
            ("Comida", "Compra en tienda/restaurante"),
            ("Transporte", "Recarga transporte / Uber personal"),
            ("Entretenimiento", "Salida / streaming / cafe"),
        ]
        cat_name, cat_desc = random.choice(categories)
        ts = date.replace(hour=random.randint(8, 21), minute=random.randint(0, 59), second=0)
        transactions.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id, "timestamp": ts.isoformat(),
            "amount": round(-amount, 2), "currency": CURRENCY_DEFAULT,
            "type": "gasto_variable", "income_source": "",
            "payment_method": random.choice(["Debit_Card", "Cash", "E-Wallet"]),
            "description": cat_desc,
        })
    return transactions


# ════════════════════════════════════════════════════════════
# GENERADORES PRINCIPALES
# ════════════════════════════════════════════════════════════

def generate_expenses_for_user(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Genera gastos fijos (clase Expense) segun el sector del usuario."""
    user_id = user["user_id"]
    sector = user["primary_sector"]
    templates = EXPENSE_TEMPLATES.get(sector, EXPENSE_TEMPLATES["Delivery"])

    expenses = []
    for tmpl in templates:
        expenses.append({
            "expense_id": f"EXP-{uuid.uuid4().hex[:6].upper()}",
            "user_id": user_id,
            "name": tmpl["name"],
            "amount": tmpl["amount"],
            "due_day_of_month": tmpl["due_day_of_month"],
            "category": tmpl["category"],
            "is_active": True,
        })
    return expenses


def generate_transactions_for_user(
    user: Dict[str, Any],
    days_history: int = DEFAULT_DAYS_HISTORY,
) -> List[Dict[str, Any]]:
    """Genera historial de transacciones (ingresos + gastos variables)."""
    user_id = user["user_id"]
    sector = user["primary_sector"]
    income_gen = INCOME_GENERATORS.get(sector, _generate_delivery_income)

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=days_history)

    all_transactions: List[Dict[str, Any]] = []
    current_date = start_date
    while current_date <= today:
        income_txns = income_gen(current_date, user_id)
        all_transactions.extend(income_txns)
        expense_txns = _generate_variable_expenses(current_date, user_id)
        all_transactions.extend(expense_txns)
        current_date += timedelta(days=1)

    all_transactions.sort(key=lambda t: t["timestamp"])
    return all_transactions


def calculate_artificial_salary(transactions: List[Dict[str, Any]]) -> float:
    """Calcula el salario artificial: mediana de ingresos mensuales."""
    income_txns = [t for t in transactions if t["type"] == "ingreso"]
    if not income_txns:
        return 0.0

    monthly_income: Dict[str, float] = {}
    for txn in income_txns:
        month_key = txn["timestamp"][:7]
        monthly_income[month_key] = monthly_income.get(month_key, 0.0) + txn["amount"]

    if not monthly_income:
        return 0.0
    return round(float(np.median(list(monthly_income.values()))), 2)


def generate_all_data(
    num_users: int = DEFAULT_NUM_USERS,
    days_history: int = DEFAULT_DAYS_HISTORY,
) -> Dict[str, Any]:
    """Genera el dataset completo: usuarios, transacciones y gastos."""
    users_data: List[Dict[str, Any]] = []
    all_transactions: List[Dict[str, Any]] = []
    all_expenses: List[Dict[str, Any]] = []

    profiles = USER_PROFILES[:num_users]

    for user in profiles:
        txns = generate_transactions_for_user(user, days_history)
        all_transactions.extend(txns)

        user_copy = dict(user)
        user_copy["artificial_salary"] = calculate_artificial_salary(txns)
        users_data.append(user_copy)

        expenses = generate_expenses_for_user(user)
        all_expenses.extend(expenses)

    return {
        "users": users_data,
        "transactions": all_transactions,
        "expenses": all_expenses,
    }


# ════════════════════════════════════════════════════════════
# CARGA A DYNAMODB (Opcional)
# ════════════════════════════════════════════════════════════

def _convert_floats_to_decimal(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte float -> Decimal para compatibilidad con DynamoDB."""
    converted = {}
    for key, value in item.items():
        if isinstance(value, float):
            converted[key] = Decimal(str(value))
        elif isinstance(value, dict):
            converted[key] = _convert_floats_to_decimal(value)
        else:
            converted[key] = value
    return converted


def upload_to_dynamodb(data: Dict[str, Any]) -> None:
    """Sube los datos generados a las tablas DynamoDB correspondientes."""
    if not BOTO3_AVAILABLE:
        print("[ERROR] boto3 no esta instalado. Instalalo con: pip install boto3")
        return

    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

    table_users = dynamodb.Table(DYNAMODB_TABLE_USERS)
    print(f"\nSubiendo {len(data['users'])} usuarios a {DYNAMODB_TABLE_USERS}...")
    with table_users.batch_writer() as batch:
        for user in data["users"]:
            batch.put_item(Item=_convert_floats_to_decimal(user))
    print("   [OK] Usuarios cargados.")

    table_txns = dynamodb.Table(DYNAMODB_TABLE_TRANSACTIONS)
    print(f"\nSubiendo {len(data['transactions'])} transacciones a {DYNAMODB_TABLE_TRANSACTIONS}...")
    with table_txns.batch_writer() as batch:
        for txn in data["transactions"]:
            batch.put_item(Item=_convert_floats_to_decimal(txn))
    print("   [OK] Transacciones cargadas.")

    table_expenses = dynamodb.Table(DYNAMODB_TABLE_EXPENSES)
    print(f"\nSubiendo {len(data['expenses'])} gastos a {DYNAMODB_TABLE_EXPENSES}...")
    with table_expenses.batch_writer() as batch:
        for exp in data["expenses"]:
            batch.put_item(Item=_convert_floats_to_decimal(exp))
    print("   [OK] Gastos cargados.")

    print("\nCarga completa a DynamoDB.")


# ════════════════════════════════════════════════════════════
# CARGA A S3 (Opcional)
# ════════════════════════════════════════════════════════════

def upload_to_s3(data: Dict[str, Any], bucket: str) -> None:
    """Sube los datos generados a un bucket S3 como archivos JSON.
    Estructura en S3:
      s3://<bucket>/incomia_data/users.json
      s3://<bucket>/incomia_data/transactions.json
      s3://<bucket>/incomia_data/expenses.json
    """
    if not BOTO3_AVAILABLE:
        print("[ERROR] boto3 no esta instalado. Instalalo con: pip install boto3")
        return

    s3_client = boto3.client("s3", region_name=AWS_REGION)

    datasets = {
        "users.json": data["users"],
        "transactions.json": data["transactions"],
        "expenses.json": data["expenses"],
    }

    print(f"\nSubiendo datos a S3 bucket: {bucket}")

    for filename, records in datasets.items():
        key = f"{S3_PREFIX}{filename}"
        body = json.dumps(records, ensure_ascii=False, indent=2, cls=DecimalEncoder)

        try:
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType="application/json",
            )
            print(f"   [OK] s3://{bucket}/{key} ({len(records)} registros)")
        except ClientError as e:
            print(f"   [ERROR] No se pudo subir {key}: {e}")
            return

    print(f"\nCarga completa a S3. Prefijo: s3://{bucket}/{S3_PREFIX}")


# ════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ════════════════════════════════════════════════════════════

def print_summary(data: Dict[str, Any]) -> None:
    """Imprime un resumen legible de los datos generados."""
    print("\n" + "=" * 60)
    print("  INCOMIA -- Resumen de Datos Generados")
    print("=" * 60)

    print(f"\n  Usuarios:       {len(data['users'])}")
    print(f"  Transacciones:  {len(data['transactions'])}")
    print(f"  Gastos fijos:   {len(data['expenses'])}")

    print("\n  -- Detalle por usuario --")
    for user in data["users"]:
        uid = user["user_id"]
        user_txns = [t for t in data["transactions"] if t["user_id"] == uid]
        income_total = sum(t["amount"] for t in user_txns if t["type"] == "ingreso")
        expense_total = sum(abs(t["amount"]) for t in user_txns if t["type"] == "gasto_variable")

        print(f"\n  [{uid}] Sector: {user['primary_sector']}")
        print(f"    Salario Artificial:   ${user['artificial_salary']:,.2f} MXN")
        print(f"    Fondo Estabilizacion: ${user['stabilization_fund_balance']:,.2f} MXN")
        print(f"    Risk Score:           {user['current_risk_score']}/100")
        print(f"    Ingresos totales:     ${income_total:,.2f} MXN ({len([t for t in user_txns if t['type'] == 'ingreso'])} txns)")
        print(f"    Gastos variables:     ${expense_total:,.2f} MXN ({len([t for t in user_txns if t['type'] == 'gasto_variable'])} txns)")

    print("\n" + "=" * 60)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def main():
    parser = argparse.ArgumentParser(description="Incomia -- Simulador de Ingresos para Economia Gig")
    parser.add_argument("--users", type=int, default=DEFAULT_NUM_USERS, help=f"Numero de usuarios (max {len(USER_PROFILES)})")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS_HISTORY, help="Dias de historial")
    parser.add_argument("--output", type=str, default=None, help="Ruta del archivo JSON de salida")
    parser.add_argument("--upload", action="store_true", help="Subir datos a DynamoDB")
    parser.add_argument("--s3-bucket", type=str, default=None, help="Nombre del bucket S3 para subir datos")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para reproducibilidad")

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    print("\nGenerando datos sinteticos para Incomia...")
    data = generate_all_data(num_users=args.users, days_history=args.days)
    print_summary(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        print(f"\nDatos guardados en: {args.output}")

    if args.upload:
        upload_to_dynamodb(data)

    if args.s3_bucket:
        upload_to_s3(data, args.s3_bucket)

    print("\nMuestra de transacciones (primeras 3):")
    for txn in data["transactions"][:3]:
        print(json.dumps(txn, indent=2, ensure_ascii=False))

    return data


if __name__ == "__main__":
    main()
