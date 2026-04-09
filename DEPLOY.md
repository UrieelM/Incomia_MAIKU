# Incomia — Guía de Despliegue Completo

Guía paso a paso para desplegar la stack completa de Incomia:
**Frontend (React) + Backend (Lambda) + IA (Bedrock + Prophet) + Infraestructura (Terraform/AWS)**

---

## Requisitos previos

| Herramienta | Versión mínima | Propósito |
|-------------|---------------|-----------|
| AWS CLI | 2.x | Despliegue en AWS |
| Terraform | 1.6+ | Infraestructura como código |
| Node.js | 18+ | Build del frontend |
| Python | 3.11 | Empaquetado de Lambdas |
| Git | — | Control de versiones |

Configura tus credenciales de AWS antes de continuar:

```bash
aws configure
# AWS Access Key ID: <tu_key>
# AWS Secret Access Key: <tu_secret>
# Default region: us-east-1
# Default output format: json
```

---

## Paso 1 — Bucket S3 de estado de Terraform (solo primera vez)

El backend de Terraform guarda su estado en S3. Debes crear el bucket **manualmente** antes del primer `terraform init`:

```bash
aws s3 mb s3://incomia-tfstate --region us-east-1
aws s3api put-bucket-versioning \
  --bucket incomia-tfstate \
  --versioning-configuration Status=Enabled
```

---

## Paso 2 — Capa de numpy/pandas para Lambda (solo primera vez)

Las Lambdas `get_forecast` y `get_ai_advice` necesitan `numpy` (y opcionalmente `prophet`).
AWS proporciona una capa gestionada con numpy/pandas para Python 3.11.

**Opción A — Capa AWS gestionada (recomendada para dev/staging):**

```bash
# Obtener el ARN más reciente de la capa AWSSDKPandas-Python311
aws lambda list-layers \
  --compatible-runtime python3.11 \
  --query "Layers[?contains(LayerName,'Pandas')].{ARN:LatestMatchingVersion.LayerVersionArn}" \
  --output table
```

Guarda el ARN — lo necesitarás en el Paso 4.

**Opción B — Capa propia con Prophet (para producción):**

```bash
mkdir -p /tmp/incomia-layer/python
pip install numpy pandas prophet --target /tmp/incomia-layer/python \
  --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11

cd /tmp/incomia-layer
zip -r layer.zip python/

aws lambda publish-layer-version \
  --layer-name incomia-ml-python311 \
  --description "numpy, pandas, prophet para Incomia" \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

Guarda el ARN del output anterior.

---

## Paso 3 — Variables de Terraform

Crea el archivo `infrastructure/terraform.tfvars` (no lo commitees, ya está en `.gitignore`):

```hcl
# infrastructure/terraform.tfvars

aws_region       = "us-east-1"
env              = "dev"                    # o "prod"
project_name     = "incomia"
tfstate_bucket   = "incomia-tfstate"
lambda_role_name = "incomia-lambda-exec"

# Modelo Bedrock para clasificación y asesor IA
# Nova Lite para clasificación es más barato; Nova Pro para el asesor
bedrock_model_id = "amazon.nova-pro-v1:0"

# API Key de INEGI (se puede poner placeholder y actualizar después)
inegi_api_key_value = "TU_API_KEY_INEGI"   # https://www.inegi.org.mx/app/api/indicadores/interna_v1_1/tokenVerify.aspx

# ARN de la capa numpy/pandas obtenida en el Paso 2
# Déjalo vacío ("") para usar el fallback estático sin predicción real
pandas_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:21"
```

---

## Paso 4 — Inicializar y aplicar Terraform

```bash
cd infrastructure/

# Inicializar (solo primera vez o cuando cambies módulos)
terraform init

# Revisar los cambios antes de aplicar
terraform plan -var-file="terraform.tfvars"

# Aplicar la infraestructura
terraform apply -var-file="terraform.tfvars"
```

Guarda los **outputs** al finalizar. Los necesitarás para el frontend:

```
Outputs:
  api_gateway_url      = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com"
  cognito_user_pool_id = "us-east-1_XXXXXXXXX"
  cognito_client_id    = "XXXXXXXXXXXXXXXXXXXXXXXXXX"

Outputs:

alerts_table_name = "incomia-alerts-dev"
analyze_expenses_function_arn = "arn:aws:lambda:us-east-1:834088498700:function:incomia-analyze-expenses-dev"
api_endpoint = "https://p70gn8n0wg.execute-api.us-east-1.amazonaws.com"
cognito_client_id = "2ildco2vbcspsnjuvr4vtnpd"
cognito_user_pool_id = "us-east-1_nS4ukF5uR"
datalake_bucket = "incomia-datalake-dev"
frontend_bucket = "incomia-frontend-dev"
lambda_role_arn = "arn:aws:iam::834088498700:role/incomia-lambda-exec"
lambda_shared_layer_arn = "arn:aws:lambda:us-east-1:834088498700:layer:incomia-shared:1"
ssm_inegi_key_name = "/incomia/inegi_api_key"
transactions_table_name = "incomia-transactions-dev"
users_table_name = "incomia-users-dev"

```

---

## Paso 5 — Variables de entorno del Frontend

Crea el archivo `frontend/.env.local` (no lo commitees):

```env
# frontend/.env.local

# URL base de API Gateway (del output de Terraform, Paso 4)
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com

# Cognito (del output de Terraform, Paso 4)
VITE_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

> **Nota:** Si `VITE_API_BASE_URL` no está definida, la app corre en modo mock
> (datos simulados) sin necesidad de AWS. Ideal para desarrollo local.

---

## Paso 6 — Instalar dependencias y build del Frontend

```bash
cd frontend/

npm install

# Desarrollo local (modo mock sin AWS)
npm run dev

# Build de producción
npm run build
```

---

## Paso 7 — Subir el Frontend a S3

Terraform ya creó el bucket S3 para el frontend. Sube el build:

```bash
cd frontend/

# Obtener el nombre del bucket del output de Terraform
BUCKET=$(cd ../infrastructure && terraform output -raw frontend_bucket_name)

# Subir los archivos
aws s3 sync dist/ s3://$BUCKET/ --delete

# Invalidar caché de CloudFront si aplica
# aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"
```

---

## Paso 8 — Habilitar modelos Bedrock (primera vez)

Los modelos de Amazon Bedrock requieren habilitación manual en la consola:

1. Ir a **AWS Console → Amazon Bedrock → Model access**
2. Habilitar: **Amazon Nova Pro** (`amazon.nova-pro-v1:0`)
3. Habilitar: **Amazon Nova Lite** (`amazon.nova-lite-v1:0`) — usado por `log_expense`
4. Esperar aprobación (generalmente instantánea para modelos Amazon)

---

## Paso 9 — Verificar el despliegue

### Backend — Prueba rápida

```bash
# Reemplaza con tu API Gateway URL
API=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com

# Crear usuario de prueba
curl -X POST "$API/users" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@incomia.mx","mode":"suggestion","salary_frequency":"monthly"}'

# Respuesta esperada:
# {"userId":"...","name":"Test User","simulated_salary":0,...}
```

### Lambdas — Ver logs

```bash
# Logs en tiempo real de una Lambda (reemplaza el nombre)
aws logs tail /aws/lambda/incomia-get-forecast-dev --follow
aws logs tail /aws/lambda/incomia-get-ai-advice-dev --follow
```

### EventBridge — Verificar el bus personalizado

```bash
aws events list-event-buses \
  --query "EventBuses[?contains(Name,'incomia')]"
```

---

## Paso 10 — Primer login en la app

1. Navegar a tu URL del frontend (S3/CloudFront)
2. Registrar una cuenta en **Register**
3. Verificar el email con el código de 6 dígitos
4. Iniciar sesión
5. En la barra lateral, hacer click en **Asesor IA** → verificar que carga el pronóstico y el consejo

---

## Arquitectura desplegada

```
Frontend (React)
    │
    ├── GET /users/{userId}/dashboard        → Lambda: get_dashboard
    ├── POST /users/{userId}/income          → Lambda: log_income
    ├── POST /users/{userId}/expense         → Lambda: log_expense (Bedrock: clasificación)
    ├── POST /users/{userId}/analyze         → Lambda: analyze_expenses (Bedrock)
    ├── GET /users/{userId}/inflation        → Lambda: inflation_alert (INEGI)
    ├── GET /users/{userId}/ai/forecast  ──→ Lambda: get_forecast
    │                                              │
    │                              EventBridge: ForecastReady
    │                                              │
    └── GET /users/{userId}/ai/advice   ←── Lambda: get_ai_advice (Bedrock: Nova Pro)

Pipeline automático EventBridge:
  EventBridge (cada lunes 9am UTC) → Lambda: analyze_expenses
  Lambda: get_forecast → EventBridge bus: incomia-events → Lambda: get_ai_advice
```

---

## Comandos útiles

```bash
# Ver outputs de Terraform
cd infrastructure && terraform output

# Destruir toda la infraestructura (cuidado en prod)
terraform destroy -var-file="terraform.tfvars"

# Actualizar solo las Lambdas (sin tocar DynamoDB/Cognito)
terraform apply -var-file="terraform.tfvars" -target=module.lambda

# Invocar manualmente una Lambda
aws lambda invoke \
  --function-name incomia-get-forecast-dev \
  --payload '{"pathParameters":{"userId":"test-user-123"}}' \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json

# Ver todas las Lambdas del proyecto
aws lambda list-functions \
  --query "Functions[?starts_with(FunctionName,'incomia')].FunctionName"
```

---

## Troubleshooting

**Error: "numpy no disponible"**
→ Agrega `pandas_layer_arn` en `terraform.tfvars` con el ARN del Paso 2.
→ El fallback estático sigue funcionando — solo sin predicción real.

**Error: "Circuit Breaker OPEN"**
→ Bedrock falló 3+ veces. Espera 60s o reinvoca para pasar a HALF_OPEN.
→ Verifica que el modelo está habilitado en Bedrock (Paso 8).

**Error: "DYNAMODB_ERROR"**
→ Verifica que las tablas existen: `aws dynamodb list-tables`
→ Verifica que el rol Lambda tiene permisos: revisa `iam.tf`.

**Error: "USER_NOT_FOUND" en get_forecast**
→ El userId del JWT de Cognito debe coincidir con el PK en DynamoDB.
→ Confirma que el usuario fue creado con `POST /users` al registrarse.

**Frontend muestra datos mock**
→ `VITE_API_BASE_URL` no está definida en `.env.local`. Agrégala.

---

*Documentación generada para Incomia — Equipo HAIKU*
