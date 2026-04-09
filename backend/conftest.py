# tests/aws_mock.py
import boto3
from moto import mock_aws

@mock_aws
def crear_tabla_mock():
    ddb = boto3.resource('dynamodb', region_name='us-east-1')
    tabla = ddb.create_table(
        TableName='incomia-usuarios',
        KeySchema=[{'AttributeName': 'uid', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'uid', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    return tabla