output "api_endpoint" {
  description = "URL base del API Gateway"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "authorizer_id" {
  description = "ID del authorizer Cognito (necesario para proteger rutas)"
  value       = aws_apigatewayv2_authorizer.cognito.id
}
