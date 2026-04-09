"""
Lambda 1: create_user
Endpoint: POST /users

Crea un nuevo usuario en incomia-users con valores iniciales.
"""
import json
import uuid
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.db import put_user, get_table, USERS_TABLE

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

VALID_MODES = {"auto", "suggestion", "educational"}
VALID_FREQUENCIES = {"weekly", "biweekly", "monthly"}


def lambda_handler(event, context):
    # Manejo de preflight OPTIONS (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        # Parsear body
        body = _parse_body(event)

        # Validar campos requeridos
        name = body.get("name", "").strip()
        email = body.get("email", "").strip()
        mode = body.get("mode", "suggestion")
        salary_frequency = body.get("salary_frequency", "monthly")

        if not name or not email:
            return _error(400, "MISSING_FIELDS", "Los campos 'name' y 'email' son requeridos.")

        if mode not in VALID_MODES:
            return _error(400, "INVALID_MODE", f"mode debe ser: {', '.join(VALID_MODES)}")

        if salary_frequency not in VALID_FREQUENCIES:
            return _error(400, "INVALID_FREQUENCY", f"salary_frequency debe ser: {', '.join(VALID_FREQUENCIES)}")

        # Crear usuario
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        user = {
            "userId": user_id,
            "name": name,
            "email": email,
            "mode": mode,
            "salary_frequency": salary_frequency,
            "simulated_salary": 0,
            "reserve_balance": 0,
            "reserve_status": "green",
            "created_at": now,
        }

        put_user(user)

        response_body = {
            "userId": user_id,
            "name": name,
            "email": email,
            "mode": mode,
            "salary_frequency": salary_frequency,
            "simulated_salary": 0,
            "reserve_balance": 0,
            "reserve_status": "green",
            "created_at": now,
        }

        return {
            "statusCode": 201,
            "headers": CORS_HEADERS,
            "body": json.dumps(response_body),
        }

    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("DYNAMODB_ERROR"):
            return _error(500, "DYNAMODB_ERROR", error_msg)
        return _error(500, "INTERNAL_ERROR", f"Error interno: {error_msg}")


def _parse_body(event: dict) -> dict:
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body) if body else {}
    return body or {}


def _error(status_code: int, code: str, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
