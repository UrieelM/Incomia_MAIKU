# =====================================================================
# ROL DE EJECUCIÓN (LAMBDA ROLE)
# En AWS, los componentes tienen política de "cero confianza".
# Este rol es el salvoconducto de nuestras funciones Serverless (Backend).
# =====================================================================

# 1. Definición del Rol: Declaramos que el servicio Lambda es quien
#    está autorizado a "asumir" este sombrero de permisos (Trust Policy).
resource "aws_iam_role" "lambda_exec" {
  name = var.lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 2. Política de Permisos: Le otorgamos las "llaves" a Lambda de los 5 pilares:
#    - DynamoDB   → Lectura/escritura en las 3 tablas del proyecto
#    - S3         → Depósito y extracción del Data Lake
#    - Bedrock    → Invocación de los modelos IA (análisis y clasificación)
#    - CloudWatch → Escritura de logs para observabilidad e instrumentación
#    - SSM        → Lectura del parámetro con la API Key de INEGI (inflation_alert)
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.lambda_role_name}-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # DynamoDB: acceso completo a las tablas del proyecto
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/${var.project_name}-*"
        ]
      },
      # S3: acceso al Data Lake del proyecto
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      },
      # Bedrock: invocación de modelos IA para clasificación y análisis
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "*"
      },
      # CloudWatch Logs: creación y escritura de grupos y streams de logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.project_name}-*"
      },
      # SSM Parameter Store: lectura del parámetro de API Key de INEGI
      # Requerido por la función inflation_alert
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/incomia/*"
      },
      # EventBridge: publicar eventos al bus personalizado incomia-events
      # Requerido por get_forecast (ForecastReady) y get_ai_advice
      {
        Effect   = "Allow"
        Action   = ["events:PutEvents"]
        Resource = "arn:aws:events:*:*:event-bus/${var.project_name}-events-*"
      },
      # Athena & Glue: consulta de datos en el Data Lake
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:ListQueryExecutions",
          "athena:GetWorkGroup",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchCreatePartition",
          "glue:CreatePartition"
        ]
        Resource = "*"
      }
    ]
  })
}

