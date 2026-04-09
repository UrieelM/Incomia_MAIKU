# =====================================================================
# OUTPUTS GLOBALES DE INFRAESTRUCTURA
# Expone los valores clave que necesita el frontend y el equipo de DevOps.
# =====================================================================

# API Gateway
output "api_endpoint" {
  description = "URL base del API Gateway (úsala en el frontend como VITE_API_URL)"
  value       = module.api_gateway.api_endpoint
}

# Cognito
output "cognito_user_pool_id" {
  description = "ID del User Pool de Cognito"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "ID del cliente Cognito (para el frontend)"
  value       = module.cognito.user_pool_client
}

# IAM
output "lambda_role_arn" {
  description = "ARN del rol IAM asignado a las Lambdas"
  value       = aws_iam_role.lambda_exec.arn
}

# S3
output "frontend_bucket" {
  description = "Nombre del bucket S3 del frontend"
  value       = module.s3.frontend_bucket_name
}

output "datalake_bucket" {
  description = "Nombre del bucket S3 del data lake"
  value       = module.s3.datalake_bucket_name
}

# DynamoDB
output "users_table_name" {
  description = "Nombre de la tabla DynamoDB de usuarios"
  value       = module.dynamodb.users_table_name
}

output "transactions_table_name" {
  description = "Nombre de la tabla DynamoDB de transacciones"
  value       = module.dynamodb.transactions_table_name
}

output "alerts_table_name" {
  description = "Nombre de la tabla DynamoDB de alertas"
  value       = module.dynamodb.alerts_table_name
}

# Lambda
output "lambda_shared_layer_arn" {
  description = "ARN del Lambda Layer compartido (incomia-shared)"
  value       = module.lambda.shared_layer_arn
}

output "analyze_expenses_function_arn" {
  description = "ARN de la función analyze_expenses (disparada por EventBridge)"
  value       = module.lambda.analyze_expenses_function_arn
}

# SSM
output "ssm_inegi_key_name" {
  description = "Nombre del parámetro SSM con la API Key de INEGI"
  value       = module.ssm.inegi_api_key_name
}
