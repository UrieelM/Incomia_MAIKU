variable "project_name" {
  description = "Nombre del proyecto usado como prefijo en la API"
  type        = string
}

variable "cognito_client_id" {
  description = "ID del cliente Cognito para el authorizer JWT"
  type        = string
}

variable "cognito_pool_id" {
  description = "ID del User Pool de Cognito para el authorizer JWT"
  type        = string
}

variable "region" {
  description = "Región AWS donde vive el User Pool de Cognito"
  type        = string
}
