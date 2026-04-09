"""
mock_data/seed.py
Script para insertar datos de demo en DynamoDB.

Uso: python seed.py
Puede ejecutarse múltiples veces sin duplicar datos (usa userId fijo).

USUARIO MOCK 1 — Carlos Mendoza (fotógrafo, mes bueno)
USUARIO MOCK 2 — Ana Torres (actriz, mes malo, reserva en rojo)
"""
import boto3
import json
from decimal import Decimal
from datetime import datetime, timezone

# ── Configuración ─────────────────────────────────────────────────────────────
AWS_REGION = "us-east-1"
USERS_TABLE = "incomia-users"
TRANSACTIONS_TABLE = "incomia-transactions"
ALERTS_TABLE = "incomia-alerts"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
users_table = dynamodb.Table(USERS_TABLE)
transactions_table = dynamodb.Table(TRANSACTIONS_TABLE)
alerts_table = dynamodb.Table(ALERTS_TABLE)


def upsert(table, item):
    """Inserta o reemplaza un ítem (idempotente)."""
    table.put_item(Item=item)
    print(f"  ✓ {list(item.values())[:2]}")


def seed_carlos():
    """Carlos Mendoza — fotógrafo freelance, mes bueno, reserva verde."""
    print("\n── USUARIO 1: Carlos Mendoza (mock-user-carlos) ──")

    user = {
        "userId": "mock-user-carlos",
        "name": "Carlos Mendoza",
        "email": "carlos@fotografo.mx",
        "mode": "suggestion",
        "salary_frequency": "biweekly",
        "simulated_salary": Decimal("5708"),   # ~$5,708 quincenales
        "reserve_balance": Decimal("12400"),
        "reserve_status": "green",
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    upsert(users_table, user)

    # Ingresos últimos 6 meses
    income_records = [
        ("2024-01-15", 18000, "Boda Hernández - Fotografía"),
        ("2024-02-10", 3500, "Sesión familiar García"),
        ("2024-03-05", 12000, "Boda Ramírez"),
        ("2024-03-20", 10000, "Quinceañera López"),
        ("2024-04-12", 6000, "Sesión corporativa BBVA"),
        ("2024-05-08", 15000, "Boda Martínez"),
        ("2024-06-18", 4500, "Sesión graduación UAM"),
    ]

    for i, (date, amount, merchant) in enumerate(income_records):
        tid = f"income-carlos-{i:03d}#{date}"
        upsert(transactions_table, {
            "userId": "mock-user-carlos",
            "transactionId": tid,
            "type": "income",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": "income",
            "category_label": "Ingreso",
            "date": date,
            "source": "manual",
            "notes": "",
            "created_at": f"{date}T10:00:00+00:00",
        })

    # Gastos del mes actual (mix primary y secondary)
    expense_records = [
        # (date, amount, merchant, category, category_label, source, notes)
        ("2024-06-01", 4500, "WALMART", "primary", "Alimentación", "bank", ""),
        ("2024-06-03", 180, "STARBUCKS", "secondary", "Cafeterías y restaurantes", "bank", "café con cliente"),
        ("2024-06-05", 2800, "CFE", "primary", "Renta y servicios", "bank", ""),
        ("2024-06-07", 890, "UBER EATS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-09", 199, "NETFLIX", "secondary", "Entretenimiento", "bank", ""),
        ("2024-06-10", 149, "SPOTIFY", "secondary", "Entretenimiento", "bank", ""),
        ("2024-06-12", 1200, "TELMEX", "primary", "Renta y servicios", "bank", "internet"),
        ("2024-06-13", 180, "STARBUCKS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-15", 650, "GASOLINERA PEMEX", "primary", "Transporte", "bank", ""),
        ("2024-06-16", 180, "STARBUCKS", "secondary", "Cafeterías y restaurantes", "bank", "reunión cliente"),
        ("2024-06-18", 890, "UBER EATS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-19", 3200, "CFE", "primary", "Renta y servicios", "bank", "electricidad estudio"),
        ("2024-06-20", 890, "UBER EATS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-22", 890, "UBER EATS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-24", 350, "FARMACIA GUADALAJARA", "primary", "Salud", "bank", "medicamentos"),
    ]

    for i, (date, amount, merchant, cat, cat_label, source, notes) in enumerate(expense_records):
        tid = f"expense-carlos-{i:03d}#{date}"
        upsert(transactions_table, {
            "userId": "mock-user-carlos",
            "transactionId": tid,
            "type": "expense",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": cat,
            "category_label": cat_label,
            "date": date,
            "source": source,
            "notes": notes,
            "created_at": f"{date}T12:00:00+00:00",
        })

    print(f"  Carlos: {len(income_records)} ingresos + {len(expense_records)} gastos insertados.")


def seed_ana():
    """Ana Torres — actriz freelance, mes malo, reserva en rojo."""
    print("\n── USUARIO 2: Ana Torres (mock-user-ana) ──")

    user = {
        "userId": "mock-user-ana",
        "name": "Ana Torres",
        "email": "ana@actriz.mx",
        "mode": "educational",
        "salary_frequency": "monthly",
        "simulated_salary": Decimal("8200"),
        "reserve_balance": Decimal("0"),
        "reserve_status": "red",
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    upsert(users_table, user)

    # Ingresos irregulares y caóticos
    income_records = [
        ("2024-01-20", 25000, "Telenovela Televisa - Cap. 1-10"),
        ("2024-03-08", 5000, "Comercial Coca-Cola"),
        ("2024-04-15", 3000, "Doblaje videojuego"),
        ("2024-05-30", 2000, "Workshop actuación"),
    ]

    for i, (date, amount, merchant) in enumerate(income_records):
        tid = f"income-ana-{i:03d}#{date}"
        upsert(transactions_table, {
            "userId": "mock-user-ana",
            "transactionId": tid,
            "type": "income",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": "income",
            "category_label": "Ingreso",
            "date": date,
            "source": "manual",
            "notes": "",
            "created_at": f"{date}T10:00:00+00:00",
        })

    # Gastos del mes actual (varios, con reserva agotada)
    expense_records = [
        ("2024-06-02", 6500, "RENTA DEPARTAMENTO", "primary", "Renta y servicios", "bank", ""),
        ("2024-06-05", 2200, "SUPER LA COMER", "primary", "Alimentación", "bank", ""),
        ("2024-06-07", 450, "UBER EATS", "secondary", "Cafeterías y restaurantes", "bank", ""),
        ("2024-06-10", 1800, "CFE + TELMEX", "primary", "Renta y servicios", "bank", ""),
        ("2024-06-12", 380, "CINEPOLIS", "secondary", "Entretenimiento", "bank", ""),
        ("2024-06-15", 199, "NETFLIX", "secondary", "Entretenimiento", "bank", ""),
        ("2024-06-17", 149, "SPOTIFY", "secondary", "Suscripciones", "bank", ""),
        ("2024-06-20", 680, "RESTAURANTE LA DOCENA", "secondary", "Cafeterías y restaurantes", "bank", "cena celebración"),
        ("2024-06-22", 1100, "FARMACIA", "primary", "Salud", "bank", "medicamentos"),
    ]

    for i, (date, amount, merchant, cat, cat_label, source, notes) in enumerate(expense_records):
        tid = f"expense-ana-{i:03d}#{date}"
        upsert(transactions_table, {
            "userId": "mock-user-ana",
            "transactionId": tid,
            "type": "expense",
            "amount": Decimal(str(amount)),
            "merchant": merchant,
            "category": cat,
            "category_label": cat_label,
            "date": date,
            "source": source,
            "notes": notes,
            "created_at": f"{date}T12:00:00+00:00",
        })

    # Alerta activa de reserve_low (seen=False)
    alert = {
        "userId": "mock-user-ana",
        "alertId": "alert-ana-reserve-001#2024-06-20T08:00:00+00:00",
        "type": "reserve_low",
        "message": "Tu reserva se ha agotado. Tu sueldo simulado se ajustará este mes.",
        "data": {},
        "seen": False,
        "created_at": "2024-06-20T08:00:00+00:00",
    }
    upsert(alerts_table, alert)

    print(f"  Ana: {len(income_records)} ingresos + {len(expense_records)} gastos + 1 alerta insertados.")


if __name__ == "__main__":
    print("═" * 60)
    print("INCOMIA — Seed de datos mock")
    print("═" * 60)
    print(f"Región: {AWS_REGION}")
    print(f"Tablas: {USERS_TABLE}, {TRANSACTIONS_TABLE}, {ALERTS_TABLE}")

    try:
        seed_carlos()
        seed_ana()
        print("\n═" * 60)
        print("✅ Seed completado exitosamente.")
        print("═" * 60)
        print("\nUsuarios disponibles:")
        print("  - mock-user-carlos  (Carlos Mendoza, fotógrafo, reserva verde)")
        print("  - mock-user-ana     (Ana Torres, actriz, reserva roja)")
        print("\nEjemplo de uso:")
        print("  GET  /users/mock-user-carlos/dashboard")
        print("  POST /users/mock-user-carlos/income")
        print("  GET  /users/mock-user-ana/dashboard")
    except Exception as e:
        print(f"\n❌ Error durante el seed: {e}")
        print("Asegúrate de tener credenciales AWS configuradas y las tablas creadas.")
        raise
