output "api_endpoint" {
  description = "URL base del API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "cognito_user_pool_id" {
  description = "ID del User Pool de Cognito"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "ID del cliente Cognito (para el frontend)"
  value       = module.cognito.user_pool_client
}

output "lambda_role_arn" {
  description = "ARN del rol IAM asignado a las Lambdas"
  value       = aws_iam_role.lambda_exec.arn
}

output "frontend_bucket" {
  description = "Nombre del bucket S3 del frontend"
  value       = module.s3.frontend_bucket_name
}

output "datalake_bucket" {
  description = "Nombre del bucket S3 del data lake"
  value       = module.s3.datalake_bucket_name
}
