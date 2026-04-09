"""
shared/bedrock.py
Cliente AWS Bedrock reutilizable para todas las Lambdas de Incomia.
"""
import os
import json
import boto3
from botocore.exceptions import ClientError

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
FALLBACK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
AWS_REGION = os.environ.get("AWS_REGION_NAME", "us-east-1")

_bedrock_client = None


def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock_client


def invoke_bedrock(prompt: str, system: str = None) -> str:
    """
    Invoca Bedrock y retorna el texto de respuesta.
    Maneja errores y retorna string vacío en caso de fallo.
    Intenta con el modelo preferido; si falla, usa el fallback.
    """
    for model_id in [BEDROCK_MODEL_ID, FALLBACK_MODEL_ID]:
        try:
            return _call_model(model_id, prompt, system)
        except Exception as e:
            print(f"[bedrock] Error con modelo {model_id}: {e}")
            continue
    # Ambos modelos fallaron
    print("[bedrock] Todos los modelos fallaron. Retornando string vacío.")
    return ""


def _call_model(model_id: str, prompt: str, system: str = None) -> str:
    """Llama a un modelo específico de Bedrock."""
    client = get_bedrock_client()

    # Construir el payload según la familia del modelo
    if "amazon.nova" in model_id:
        body = _build_nova_payload(prompt, system)
    elif "anthropic" in model_id:
        body = _build_claude_payload(prompt, system)
    else:
        # Formato genérico (Messages API)
        body = _build_nova_payload(prompt, system)

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())

    # Extraer texto según la familia del modelo
    if "amazon.nova" in model_id:
        return response_body["output"]["message"]["content"][0]["text"]
    elif "anthropic" in model_id:
        return response_body["content"][0]["text"]
    else:
        return str(response_body)


def _build_nova_payload(prompt: str, system: str = None) -> dict:
    """Construye payload para Amazon Nova."""
    payload = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "inferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.1,
        },
    }
    if system:
        payload["system"] = [{"text": system}]
    return payload


def _build_claude_payload(prompt: str, system: str = None) -> dict:
    """Construye payload para Anthropic Claude (Messages API)."""
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.1,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }
    if system:
        payload["system"] = system
    return payload


def parse_json_response(text: str) -> dict | None:
    """
    Intenta parsear la respuesta de Bedrock como JSON.
    Retorna None si no es JSON válido.
    """
    if not text:
        return None
    # Limpia posibles bloques de código markdown
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Elimina primera y última línea (``` y ```)
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"[bedrock] No se pudo parsear JSON: {text[:200]}")
        return None
