# lambdas/calcular_salario/test_handler.py
import boto3, pytest
from moto import mock_aws
from decimal import Decimal
from handler import lambda_handler

# Necesario para que boto3 apunte a mock
import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'

@pytest.fixture
def tabla_dynamo():
    with mock_aws():
        ddb = boto3.resource('dynamodb', region_name='us-east-1')
        tabla = ddb.create_table(
            TableName='incomia-usuarios',
            KeySchema=[{'AttributeName': 'uid', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'uid', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        # Usuario inicial con historial
        tabla.put_item(Item={
            'uid': 'user-123',
            'historial_ingresos': ['400', '300', '500', '350'],
            'fondo_estabilizacion': '200',
            'salario_artificial': '387'
        })
        yield tabla

def test_semana_buena(tabla_dynamo):
    """Ingreso mayor al salario objetivo → excedente va al fondo"""
    with mock_aws():
        result = lambda_handler({'uid': 'user-123', 'monto': 800}, None)
        assert Decimal(result['aporte_fondo']) > 0
        assert Decimal(result['salario_artificial']) <= 800

def test_semana_mala(tabla_dynamo):
    """Ingreso menor al salario objetivo → fondo cubre el déficit"""
    with mock_aws():
        result = lambda_handler({'uid': 'user-123', 'monto': 150}, None)
        assert Decimal(result['nuevo_fondo']) < Decimal('200')
        assert Decimal(result['salario_artificial']) > 150

def test_fondo_no_va_negativo(tabla_dynamo):
    """Si el fondo no alcanza, paga lo que hay y no más"""
    with mock_aws():
        # Semana muy mala, fondo de solo $200 vs deficit de $237
        result = lambda_handler({'uid': 'user-123', 'monto': 50}, None)
        assert Decimal(result['nuevo_fondo']) >= 0