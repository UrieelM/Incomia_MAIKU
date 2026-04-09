# =====================================================================
# OUTPUTS DEL MÓDULO LAMBDA
# ARNs e información de las funciones para uso en otros módulos.
# =====================================================================

output "create_user_function_arn" {
  description = "ARN de la función create_user"
  value       = aws_lambda_function.create_user.arn
}

output "log_income_function_arn" {
  description = "ARN de la función log_income"
  value       = aws_lambda_function.log_income.arn
}

output "log_expense_function_arn" {
  description = "ARN de la función log_expense"
  value       = aws_lambda_function.log_expense.arn
}

output "get_dashboard_function_arn" {
  description = "ARN de la función get_dashboard"
  value       = aws_lambda_function.get_dashboard.arn
}

output "analyze_expenses_function_arn" {
  description = "ARN de la función analyze_expenses"
  value       = aws_lambda_function.analyze_expenses.arn
}

output "analyze_expenses_function_name" {
  description = "Nombre de la función analyze_expenses (requerido por EventBridge)"
  value       = aws_lambda_function.analyze_expenses.function_name
}

output "inflation_alert_function_arn" {
  description = "ARN de la función inflation_alert"
  value       = aws_lambda_function.inflation_alert.arn
}

output "shared_layer_arn" {
  description = "ARN del Lambda Layer compartido"
  value       = aws_lambda_layer_version.shared.arn
}

output "get_forecast_function_arn" {
  description = "ARN de la función get_forecast (pronóstico de liquidez IA)"
  value       = aws_lambda_function.get_forecast.arn
}

output "get_forecast_function_name" {
  description = "Nombre de la función get_forecast"
  value       = aws_lambda_function.get_forecast.function_name
}

output "get_ai_advice_function_arn" {
  description = "ARN de la función get_ai_advice (asesor IA Bedrock)"
  value       = aws_lambda_function.get_ai_advice.arn
}

output "get_ai_advice_function_name" {
  description = "Nombre de la función get_ai_advice"
  value       = aws_lambda_function.get_ai_advice.function_name
}
