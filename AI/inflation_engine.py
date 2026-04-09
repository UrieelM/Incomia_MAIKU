import urllib.request
import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("incomia.inflation_engine")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s | %(message)s"))
    logger.addHandler(_h)

INEGI_TOKEN = os.environ.get("INEGI_TOKEN", "mock_inegi_token")

# Mock IDs para subíndices de BIE INEGI (Banco de Información Económica)
# En producción, se usarían los catálogos exactos proporcionados por INEGI
INDICATORS = {
    "inpc_general": "628194",
    "alimentos": "628203",     # Hipotético ID para subíndice alimentos y bebidas
    "gasolina": "628220",      # Hipotético ID para gasolinas
    "telecom": "628236"        # Hipotético ID para telecomunicaciones
}

def fetch_inegi_indicator(indicator_id: str) -> float:
    """Obtiene el último valor de inflación trimestral/anualizada para un indicador BIE."""
    if INEGI_TOKEN == "mock_inegi_token":
        # Simular lectura segura sin petición real para evitar bloqueos si no hay token real
        mock_data = {
            "628194": 4.5,  # INPC General 4.5%
            "628203": 7.2,  # Alimentos 7.2%
            "628220": 5.8,  # Gasolina 5.8%
            "628236": 2.1   # Telecom 2.1%
        }
        return mock_data.get(indicator_id, 4.0)

    url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{indicator_id}/es/0700/false/BIE/2.0/{INEGI_TOKEN}?type=json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'IncomiaFintech/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            # Dependiendo del formato exacto de BIE v2, extraemos el ultimo valor (OBS_VALUE)
            # asumiendo estructura: {"Series": [{"OBSERVATIONS": [{"OBS_VALUE": "4.5"}]}]}
            series = data.get('Series', [])
            if series and series[0].get('OBSERVATIONS'):
                last_obs = series[0]['OBSERVATIONS'][-1]
                return float(last_obs.get('OBS_VALUE', 0.0))
            return 4.0
    except Exception as e:
        logger.error(f"Fallo al contactar INEGI API para {indicator_id}: {e}")
        return 4.5 # Fallback nacional general

def calculate_personalized_inflation(expenses: Dict[str, float]) -> Dict[str, Any]:
    """
    Calcula la inflación ponderada basándose en el porcentaje del gasto total del usuario
    en diferentes categorías clave vs los subíndices de INEGI.
    """
    total_spend = sum(expenses.values())
    if total_spend == 0:
        total_spend = 1 # Evitar div/0
        
    inpc_rates = {
        "alimentos": fetch_inegi_indicator(INDICATORS["alimentos"]),
        "gasolina": fetch_inegi_indicator(INDICATORS["gasolina"]),
        "telecom": fetch_inegi_indicator(INDICATORS["telecom"])
    }
    
    national_inflation = fetch_inegi_indicator(INDICATORS["inpc_general"])
    
    weighted_inflation = 0.0
    mapped_spend = 0.0
    
    for category, amount in expenses.items():
        if category in inpc_rates:
            weight = amount / total_spend
            weighted_inflation += weight * inpc_rates[category]
            mapped_spend += amount
            
    # El resto del gasto asume inflación general
    unmapped_weight = (total_spend - mapped_spend) / total_spend
    weighted_inflation += unmapped_weight * national_inflation

    return {
        "personalized_inflation": round(weighted_inflation, 2),
        "national_inflation": round(national_inflation, 2)
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Handler para calcular la pérdida de poder adquisitivo.
    """
    user_expenses = event.get("recurring_expenses", {
        "alimentos": 3000,
        "gasolina": 1500,
        "telecom": 600,
        "otros": 2000
    })
    
    current_artificial_salary = event.get("current_artificial_salary", 15000)

    try:
        inflation_data = calculate_personalized_inflation(user_expenses)
        
        # Calcular el sueldo sugerido para compensar la inflación trimestral
        p_inf = inflation_data["personalized_inflation"]
        adjustment_needed = current_artificial_salary * (p_inf / 100.0)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "personalized_inflation_rate": inflation_data["personalized_inflation"],
                "national_inflation_rate": inflation_data["national_inflation"],
                "suggested_salary_adjustment": round(adjustment_needed, 2)
            })
        }
    except Exception as e:
        logger.exception("Error al calcular inflación personalizada.")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "No se pudo calcular la inflación."})
        }

def run_local_test():
    """Prueba local simulada"""
    event = {
        "current_artificial_salary": 20000,
        "recurring_expenses": {
            "alimentos": 5000,
            "gasolina": 3000,
            "telecom": 1000,
            "otros": 1000
        }
    }
    res = lambda_handler(event, None)
    print("Resultado Motor de Inflación:")
    print(json.dumps(json.loads(res["body"]), indent=2))

if __name__ == "__main__":
    run_local_test()
