# handler.py — Lambda calcular_salario
import json, boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tabla = dynamodb.Table('incomia-usuarios')

def lambda_handler(event, context):
    uid   = event['uid']
    monto = Decimal(str(event['monto']))

    # 1. Obtener perfil del usuario
    resp   = tabla.get_item(Key={'uid': uid})
    perfil = resp['Item']

    historial        = perfil.get('historial_ingresos', [])
    fondo            = Decimal(str(perfil.get('fondo_estabilizacion', '0')))
    salario_objetivo = calcular_salario_objetivo(historial)

    # 2. Lógica de split
    if monto >= salario_objetivo:
        pago_inmediato   = salario_objetivo
        aporte_al_fondo  = monto - salario_objetivo
    else:
        deficit          = salario_objetivo - monto
        liberado         = min(fondo, deficit)
        pago_inmediato   = monto + liberado
        aporte_al_fondo  = -liberado   # negativo = retiro del fondo

    nuevo_fondo = fondo + aporte_al_fondo

    # 3. Actualizar DynamoDB
    historial.append(str(monto))
    tabla.update_item(
        Key={'uid': uid},
        UpdateExpression="SET fondo_estabilizacion = :f, historial_ingresos = :h",
        ExpressionAttributeValues={':f': nuevo_fondo, ':h': historial[-12:]}  # últimas 12 semanas
    )

    return {
        'salario_artificial': str(pago_inmediato),
        'nuevo_fondo':        str(nuevo_fondo),
        'aporte_fondo':       str(aporte_al_fondo)
    }

def calcular_salario_objetivo(historial):
    if not historial:
        return Decimal('300')  # default inicial
    valores = [Decimal(x) for x in historial[-8:]]  # últimas 8 semanas
    return sum(valores) / len(valores)   # promedio móvil simple