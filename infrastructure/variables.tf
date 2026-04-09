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
