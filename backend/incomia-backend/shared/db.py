"""
shared/db.py
Cliente DynamoDB reutilizable para todas las Lambdas de Incomia.
"""
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Nombres de tablas desde variables de entorno
USERS_TABLE = os.environ.get("USERS_TABLE", "incomia-users")
TRANSACTIONS_TABLE = os.environ.get("TRANSACTIONS_TABLE", "incomia-transactions")
ALERTS_TABLE = os.environ.get("ALERTS_TABLE", "incomia-alerts")

# Cliente DynamoDB (singleton)
_dynamodb = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"))
    return _dynamodb


def get_table(table_name: str):
    return get_dynamodb().Table(table_name)


# ──────────────────────────────────────────────
# Usuarios
# ──────────────────────────────────────────────

def get_user(user_id: str) -> dict | None:
    """Obtiene un usuario por userId. Retorna None si no existe."""
    try:
        response = get_table(USERS_TABLE).get_item(Key={"userId": user_id})
        return response.get("Item")
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def put_user(user: dict) -> None:
    """Inserta o reemplaza un usuario."""
    try:
        get_table(USERS_TABLE).put_item(Item=user)
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def update_user(user_id: str, updates: dict) -> None:
    """Actualiza campos específicos de un usuario."""
    try:
        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
        expr_names = {f"#{k}": k for k in updates}
        expr_values = {f":{k}": v for k, v in updates.items()}
        get_table(USERS_TABLE).update_item(
            Key={"userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


# ──────────────────────────────────────────────
# Transacciones
# ──────────────────────────────────────────────

def put_transaction(transaction: dict) -> None:
    """Inserta una transacción."""
    try:
        get_table(TRANSACTIONS_TABLE).put_item(Item=transaction)
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def update_transaction(user_id: str, transaction_id: str, updates: dict) -> None:
    """Actualiza campos de una transacción."""
    try:
        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
        expr_names = {f"#{k}": k for k in updates}
        expr_values = {f":{k}": v for k, v in updates.items()}
        get_table(TRANSACTIONS_TABLE).update_item(
            Key={"userId": user_id, "transactionId": transaction_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def get_user_transactions(user_id: str, type_filter: str = None) -> list:
    """
    Obtiene todas las transacciones de un usuario.
    Opcionalmente filtra por tipo ('income' o 'expense').
    Usa Scan con FilterExpression (sin paginación, restricción hackathon).
    """
    try:
        table = get_table(TRANSACTIONS_TABLE)
        filter_expr = Attr("userId").eq(user_id)
        if type_filter:
            filter_expr = filter_expr & Attr("type").eq(type_filter)
        response = table.scan(FilterExpression=filter_expr)
        return response.get("Items", [])
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def get_transactions_by_date_range(user_id: str, start_date: str, end_date: str, type_filter: str = None) -> list:
    """
    Obtiene transacciones de un usuario dentro de un rango de fechas (ISO 8601).
    """
    try:
        table = get_table(TRANSACTIONS_TABLE)
        filter_expr = (
            Attr("userId").eq(user_id)
            & Attr("date").gte(start_date)
            & Attr("date").lte(end_date)
        )
        if type_filter:
            filter_expr = filter_expr & Attr("type").eq(type_filter)
        response = table.scan(FilterExpression=filter_expr)
        return response.get("Items", [])
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


# ──────────────────────────────────────────────
# Alertas
# ──────────────────────────────────────────────

def put_alert(alert: dict) -> None:
    """Inserta una alerta."""
    try:
        get_table(ALERTS_TABLE).put_item(Item=alert)
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def get_unseen_alerts(user_id: str) -> list:
    """Obtiene alertas no vistas (seen=false) de un usuario."""
    try:
        table = get_table(ALERTS_TABLE)
        filter_expr = Attr("userId").eq(user_id) & Attr("seen").eq(False)
        response = table.scan(FilterExpression=filter_expr)
        return response.get("Items", [])
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")


def get_alerts_by_type_and_date(user_id: str, alert_type: str, since_date: str) -> list:
    """Obtiene alertas de un tipo específico creadas desde una fecha dada."""
    try:
        table = get_table(ALERTS_TABLE)
        filter_expr = (
            Attr("userId").eq(user_id)
            & Attr("type").eq(alert_type)
            & Attr("created_at").gte(since_date)
        )
        response = table.scan(FilterExpression=filter_expr)
        return response.get("Items", [])
    except ClientError as e:
        raise Exception(f"DYNAMODB_ERROR: {e.response['Error']['Message']}")
