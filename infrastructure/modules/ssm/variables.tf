variable "project_name" {
  description = "Nombre del proyecto usado como prefijo en los recursos"
  type        = string
}

variable "env" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
}

variable "inegi_api_key_value" {
  description = "Valor inicial de la API Key de INEGI. Puede ser un placeholder; actualizar manualmente en producción."
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER_REEMPLAZAR_EN_AWS_CONSOLE"
}
