"""
Lambda: update_user_config
Endpoint: PATCH /users/{userId}

Actualiza la configuración del usuario (simulated_salary, salary_frequency, mode).
"""
import json
import os
import sys

# Añadir el path de la layer compartida para importar db
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.db import get_table, USERS_TABLE

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,PATCH,OPTIONS",
    "Content-Type": "application/json",
}

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        user_id = event.get("pathParameters", {}).get("userId")
        if not user_id:
            return _error(400, "MISSING_USER_ID", "Lle faltó el userId en el path.")

        body = _parse_body(event)
        
        # Campos permitidos para actualizar
        updates = {}
        if "simulated_salary" in body:
            updates["simulated_salary"] = float(body["simulated_salary"])
        if "salary_frequency" in body:
            updates["salary_frequency"] = body["salary_frequency"]
        if "mode" in body:
            updates["mode"] = body["mode"]
        if "name" in body:
            updates["name"] = body["name"]

        if not updates:
            return _error(400, "NO_UPDATES", "No se proporcionaron campos para actualizar.")

        table = get_table(USERS_TABLE)
        
        # Construir expresión de actualización dinámicamente
        update_expr = "SET "
        expr_names = {}
        expr_values = {}
        
        for k, v in updates.items():
            attr_name = f"#{k}"
            val_name = f":{k}"
            update_expr += f"{attr_name} = {val_name}, "
            expr_names[attr_name] = k
            expr_values[val_name] = v
            
        update_expr = update_expr.rstrip(", ")

        response = table.update_item(
            Key={"userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW"
        )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(response.get("Attributes", {})),
        }

    except Exception as e:
        return _error(500, "INTERNAL_ERROR", str(e))

def _parse_body(event):
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body) if body else {}
    return body or {}

def _error(status_code, code, message):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": code, "message": message}),
    }
