import json
import logging
import os
import time
from typing import Dict, Any, List

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

logger = logging.getLogger("incomia.weekly_alerts")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s | %(message)s"))
    logger.addHandler(_h)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
# Amazon Nova Pro ARN or Model ID as requested by user
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """Eres el "Motor de Alertas Semanales Inteligentes" de Incomia, pensado para cuidar el bolsillo de trabajadores freelancers y de plataformas (gig) en México de forma súper amigable.
Tu misión es revisar sus últimas transacciones (máximo 30) para ayudarles a manejar mejor su dinero sin usar ningún término financiero complicado. Trátalos con muchísima empatía; sabes que su ingreso es inestable y hacen un gran esfuerzo diario. Valora su trabajo.

REGLAS PARA TU RESPUESTA:
1. Debes retornar ÚNICAMENTE un objeto JSON totalmente válido. Sin usar bloques `json` ni texto de relleno antes o después.
2. Usa el siguiente formato estricto:
{
  "top_3_discretionary_expenses": [
    {
      "merchant": "Nombre del lugar (ej. Oxxo)",
      "amount": 0.00,
      "category": "Antojos o Varios"
    }
  ],
  "weekly_alert": "UNA ÚNICA motivación/alerta semanal. Ej. '¡Hola! Eres un guerrero. Revisando tus gastos noté que se nos fueron $400 en cafés. ¿Qué tal si la próxima semana los preparamos en casa y nos ahorramos un dinerito?'",
  "salary_adjustment_suggestion": {
     "suggested_adjustment": 0.00,
     "reason": "Explícales como a un amigo por qué deberían subir o bajar el 'sueldo artificial' de su app para estar más tranquilos este mes."
  }
}
Si ves que les va bien o que gastan de más, ajusta la sugerencia de sueldo artificial (positivo o negativo) para que se mantengan saludables.
"""

def _build_user_prompt(transactions: List[Dict[str, Any]]) -> str:
    """Construye el prompt de usuario con las transacciones."""
    transactions_str = json.dumps(transactions, indent=2, ensure_ascii=False)
    return f"""A continuación se presenta el historial de las últimas transacciones (máximo 30).
Analízalas y entrega el JSON solicitado de acuerdo a las reglas del System Prompt.
Asegúrate de deducir cuáles transacciones son gastos 'discrecionales' (ej. suscripciones, comida fuera, entretenimiento que no son de estricta supervivencia) vs fijos/esenciales.

Historial de transacciones:
{transactions_str}
"""

def get_fallback_alert(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Genera una alerta segura en caso de que Bedrock o Boto3 fallen."""
    logger.warning("Usando fallback de alertas debido a fallo de Bedrock.")
    
    # Simple regla para derivar gastos discrecionales básicos
    merchant_sums = {}
    for tx in transactions:
        amount = float(tx.get("amount", 0))
        # Asumiendo que egresos son negativos
        if amount < 0 and tx.get("category", "") not in ["renta", "servicios", "salud"]:
            m = tx.get("merchant", "Otro")
            merchant_sums[m] = merchant_sums.get(m, 0) + abs(amount)
            
    top_merchants = sorted(merchant_sums.items(), key=lambda x: x[1], reverse=True)[:3]
    top_3_discretionary = [
        {"merchant": k, "amount": v, "category": "Varios"} for k, v in top_merchants
    ]
    
    return {
        "top_3_discretionary_expenses": top_3_discretionary,
        "weekly_alert": "Mantén el control de tus gastos variables esta semana para cuidar tu sueldo artificial.",
        "salary_adjustment_suggestion": {
            "suggested_adjustment": 0.0,
            "reason": "Tus flujos parecen estables, mantén tu nivel actual por ahora."
        }
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler para generar las Alertas Inteligentes Semanales.
    Se espera que sea invocado por EventBridge o Gateway.
    """
    transactions = event.get("recent_transactions", [])
    
    # Limitar a las ultimas 30 transacciones si vienen mas
    if len(transactions) > 30:
        transactions = transactions[-30:]
        
    if not transactions:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No se proporcionaron transacciones."})
        }

    if not BOTO3_AVAILABLE:
        result = get_fallback_alert(transactions)
        return {
            "statusCode": 200,
            "body": json.dumps({"data": result, "source": "fallback", "reason": "no_boto3"})
        }

    try:
        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        user_prompt = _build_user_prompt(transactions)

        # Format payload specifically for Amazon Nova Pro
        request_body = {
            "inferenceConfig": {
                "max_new_tokens": 1000,
                "temperature": 0.2
            },
            "system": [{"text": SYSTEM_PROMPT}],
            "messages": [
                {"role": "user", "content": [{"text": user_prompt}]}
            ]
        }

        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        resp_body = json.loads(response["body"].read())
        # Amazon Nova returns output in output.message.content
        content_text = resp_body.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "").strip()

        # Limpiar posibles delimitadores markdown si Claude ignora la instruccion
        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.startswith("```"):
            content_text = content_text[3:]
        if content_text.endswith("```"):
            content_text = content_text[:-3]

        parsed_json = json.loads(content_text.strip())

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "data": parsed_json,
                "source": "bedrock"
            })
        }

    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear el JSON de Bedrock: {e}. Contenido crudo: {content_text}")
        return {
            "statusCode": 200,
            "body": json.dumps({"data": get_fallback_alert(transactions), "source": "fallback", "reason": "invalid_json"})
        }
    except Exception as e:
        logger.exception(f"Error invocando Bedrock: {e}")
        return {
            "statusCode": 200,
            "body": json.dumps({"data": get_fallback_alert(transactions), "source": "fallback", "reason": "api_error"})
        }

def run_local_test():
    """Ejecucion local simulada."""
    mock_transactions = [
        {"id": "t1", "amount": 1500, "category": "ingreso", "merchant": "DiDi", "date": "2026-04-01"},
        {"id": "t2", "amount": -300, "category": "comida", "merchant": "Starbucks", "date": "2026-04-02"},
        {"id": "t3", "amount": -150, "category": "entretenimiento", "merchant": "Netflix", "date": "2026-04-03"},
        {"id": "t4", "amount": -800, "category": "servicios", "merchant": "CFE", "date": "2026-04-04"},
        {"id": "t5", "amount": -400, "category": "comprar", "merchant": "Amazon", "date": "2026-04-05"},
    ]
    print(f"Probando alerta con modelo: {BEDROCK_MODEL_ID}")
    res = lambda_handler({"recent_transactions": mock_transactions}, None)
    print(json.dumps(json.loads(res["body"]), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_local_test()
