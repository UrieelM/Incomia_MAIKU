output "inegi_api_key_arn" {
  description = "ARN del parámetro SSM de la API Key de INEGI (para políticas IAM)"
  value       = aws_ssm_parameter.inegi_api_key.arn
}

output "inegi_api_key_name" {
  description = "Nombre del parámetro SSM de la API Key de INEGI"
  value       = aws_ssm_parameter.inegi_api_key.name
}
