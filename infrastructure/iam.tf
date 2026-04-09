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
      Principal = { Service = "lambda.amazonaws.com" } # Confianza en AWS Lambda
    }]
  })
}

# 2. Política de Permisos: Le otorgamos las "llaves" a Lambda de los 4 pilares:
#    - DynamoDB -> Lectura/escritura de base de datos de usuarios
#    - S3 -> Depósito y extracción del Data Lake
#    - Bedrock -> Invocación de los modelos IA (Anthropic/Claude)
#    - Logs -> Permisos de escritura hacia CloudWatch para la observabilidad e instrumentación
resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["dynamodb:*"],          Resource = "*" },
      { Effect = "Allow", Action = ["s3:*"],                Resource = "*" },
      { Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = "*" },
      { Effect = "Allow", Action = ["logs:*"],              Resource = "*" }
    ]
  })
}
