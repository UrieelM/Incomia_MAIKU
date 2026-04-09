# =====================================================================
# VARIABLES GLOBALES DE INFRAESTRUCTURA
# =====================================================================

variable "aws_region" {
  description = "Región AWS donde se despliegan los recursos"
  type        = string
}

variable "env" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo en todos los recursos"
  type        = string
}

variable "tfstate_bucket" {
  description = "Nombre del bucket S3 que almacena el estado de Terraform"
  type        = string
}

variable "lambda_role_name" {
  description = "Nombre del rol IAM para las funciones Lambda"
  type        = string
}

# ---------------------------------------------------------------------
# Lambda
# ---------------------------------------------------------------------

variable "lambda_code_base_path" {
  description = "Ruta relativa desde ./modules/lambda hacia el directorio raíz de incomia-backend"
  type        = string
  default     = "../../../backend/incomia-backend"
}

variable "bedrock_model_id" {
  description = "ID del modelo de Amazon Bedrock para clasificación y análisis IA"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

# ---------------------------------------------------------------------
# SSM / Secrets
# ---------------------------------------------------------------------

variable "inegi_api_key_value" {
  description = "Valor inicial de la API Key de INEGI. Se puede dejar como placeholder y actualizar manualmente en AWS Console."
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER_REEMPLAZAR_EN_AWS_CONSOLE"
}

variable "pandas_layer_arn" {
  description = <<-EOT
    ARN de la Lambda Layer con numpy/pandas para Python 3.11.
    Requerida por get_forecast para ejecutar Prophet o Moving Average.
    Ejemplo (us-east-1): arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:21
    Deja vacío ("") para usar el fallback estático (sin predicción real).
  EOT
  type        = string
  default     = ""
}
