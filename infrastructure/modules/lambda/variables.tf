# =====================================================================
# VARIABLES DEL MÓDULO LAMBDA
# =====================================================================

variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo en todas las funciones"
  type        = string
}

variable "env" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "Región AWS donde se despliegan las funciones Lambda"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN del rol IAM que asumen las funciones Lambda"
  type        = string
}

variable "api_id" {
  description = "ID del API Gateway HTTP donde se registran las rutas Lambda"
  type        = string
}

variable "authorizer_id" {
  description = "ID del authorizer JWT de Cognito para proteger las rutas"
  type        = string
}

variable "bedrock_model_id" {
  description = "ID del modelo de Amazon Bedrock para clasificación y análisis IA"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "lambda_code_base_path" {
  description = "Ruta base hacia el directorio de código Lambda (relativa a modules/lambda/)"
  type        = string
  default     = "../../../backend/incomia-backend"
}

variable "users_table_name" {
  description = "Nombre de la tabla DynamoDB de usuarios"
  type        = string
}

variable "transactions_table_name" {
  description = "Nombre de la tabla DynamoDB de transacciones"
  type        = string
}

variable "alerts_table_name" {
  description = "Nombre de la tabla DynamoDB de alertas"
  type        = string
}

variable "ssm_inegi_key_arn" {
  description = "ARN del parámetro SSM con la API key de INEGI (para inflation_alert)"
  type        = string
}

variable "pandas_layer_arn" {
  description = <<-EOT
    ARN de la Lambda Layer que contiene numpy/pandas para Python 3.11.
    Requerido por get_forecast (Prophet/Moving Average).
    Usa la capa AWS-gestionada "AWSSDKPandas-Python311" o una propia.
    Deja vacío ("") para deshabilitar — get_forecast usará fallback estático.
  EOT
  type        = string
  default     = ""
}

