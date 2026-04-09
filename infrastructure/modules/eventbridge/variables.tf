variable "project_name" {
  description = "Nombre del proyecto usado como prefijo en los recursos"
  type        = string
}

variable "env" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
}

variable "analyze_expenses_function_arn" {
  description = "ARN de la función Lambda analyze_expenses a disparar semanalmente"
  type        = string
}

variable "analyze_expenses_function_name" {
  description = "Nombre de la función Lambda analyze_expenses (para el permiso de invocación)"
  type        = string
}

variable "get_ai_advice_function_arn" {
  description = "ARN de la función Lambda get_ai_advice — destino del evento ForecastReady"
  type        = string
}

variable "get_ai_advice_function_name" {
  description = "Nombre de la función Lambda get_ai_advice (para el permiso de invocación EventBridge)"
  type        = string
}

variable "get_forecast_function_arn" {
  description = "ARN de la función Lambda get_forecast — destino del evento DataIngested"
  type        = string
}

variable "get_forecast_function_name" {
  description = "Nombre de la función Lambda get_forecast (para el permiso de invocación EventBridge)"
  type        = string
}

