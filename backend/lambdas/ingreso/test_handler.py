# lambdas/ingreso/test_handler.py
import json
from moto import mock_aws
import boto3, pytest, os

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['STATE_MACHINE_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:IncomiaFlujo'

@pytest.fixture
def setup_aws():
    with mock_aws():
        # DynamoDB
        ddb = boto3.resource('dynamodb', region_name='us-east-1')
        ddb.create_table(
            TableName='incomia-transacciones',
            KeySchema=[{'AttributeName': 'tx_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'tx_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        # Step Functions mock
        sf = boto3.client('stepfunctions', region_name='us-east-1')
        sf.create_state_machine(
            name='IncomiaFlujo',
            definition='{"Comment":"mock","StartAt":"S","States":{"S":{"Type":"Pass","End":true}}}',
            roleArn='arn:aws:iam::123456789012:role/mock'
        )
        yield

def test_post_ingreso(setup_aws):
    from handler import lambda_handler

    # Evento simulado de API Gateway
    evento = {
        'body': json.dumps({'monto': 750}),
        'requestContext': {
            'authorizer': {
                'claims': {'sub': 'user-abc'}
            }
        }
    }

    with mock_aws():
        response = lambda_handler(evento, None)

    assert response['statusCode'] == 202
    body = json.loads(response['body'])
    assert 'tx_id' in body
    assert body['status'] == 'procesando'