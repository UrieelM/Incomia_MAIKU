output "users_table_name" {
  description = "Nombre de la tabla DynamoDB de usuarios"
  value       = aws_dynamodb_table.users.name
}

output "transactions_table_name" {
  description = "Nombre de la tabla DynamoDB de transacciones"
  value       = aws_dynamodb_table.transactions.name
}

output "alerts_table_name" {
  description = "Nombre de la tabla DynamoDB de alertas"
  value       = aws_dynamodb_table.alerts.name
}
