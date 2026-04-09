# =====================================================================
# ENRUTADOR PRINCIPAL DE INFRAESTRUCTURA (MAIN)
# Aquí inicializamos nuestro proveedor en AWS y conectamos todas
# las piezas del rompecabezas (Módulos de la arquitectura Incomia).
# =====================================================================

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }

  # Configuración del Backend S3:
  # Guarda el archivo de estado ('terraform.tfstate') en la nube.
  # Requisito: El bucket definido aquí debe crearse MANUALMENTE en la consola de AWS
  # antes de ejecutar 'terraform init'. NO soporta variables.
  backend "s3" {
    bucket = "incomia-tfstate"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
}

# Inicializamos el proveedor de AWS con la región especificada
provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------
# MÓDULO DE BASE DE DATOS (DYNAMODB)
# Tablas NoSQL ultrarápidas para la persistencia del negocio.
# ---------------------------------------------------------------------
module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
  env          = var.env
}

# ---------------------------------------------------------------------
# MÓDULO DE ALMACENAMIENTO (S3)
# Almacena de manera estática el Frontend (React) y la metadata/archivos 
# pesados (Data Lake).
# ---------------------------------------------------------------------
module "s3" {
  source       = "./modules/s3"
  project_name = var.project_name
  env          = var.env
}

# ---------------------------------------------------------------------
# MÓDULO DE IDENTIDAD (COGNITO)
# Sistema de autenticación de usuarios y generación de JWTs.
# ---------------------------------------------------------------------
module "cognito" {
  source       = "./modules/cognito"
  project_name = var.project_name
}

# ---------------------------------------------------------------------
# MÓDULO DE ENRUTAMIENTO (API GATEWAY)
# El proxy HTTP desde donde recibimos el tráfico entrante del Front.
# Se integra directamente con los parámetros/ID salientes de Cognito.
# ---------------------------------------------------------------------
module "api_gateway" {
  source            = "./modules/api_gateway"
  project_name      = var.project_name
  cognito_client_id = module.cognito.user_pool_client
  cognito_pool_id   = module.cognito.user_pool_id
  region            = var.aws_region
}
