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
# Tres tablas NoSQL: usuarios, transacciones y alertas.
# ---------------------------------------------------------------------
module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
  env          = var.env
}

# ---------------------------------------------------------------------
# MÓDULO DE ALMACENAMIENTO (S3)
# Bucket para el Frontend (React SPA) y el Data Lake.
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
# API HTTP con authorizer JWT integrado con Cognito.
# Las rutas específicas son registradas por el módulo Lambda.
# ---------------------------------------------------------------------
module "api_gateway" {
  source            = "./modules/api_gateway"
  project_name      = var.project_name
  cognito_client_id = module.cognito.user_pool_client
  cognito_pool_id   = module.cognito.user_pool_id
  region            = var.aws_region
}

# ---------------------------------------------------------------------
# MÓDULO DE PARÁMETROS SEGUROS (SSM)
# Almacena la API Key de INEGI para la función inflation_alert.
# ---------------------------------------------------------------------
module "ssm" {
  source              = "./modules/ssm"
  project_name        = var.project_name
  env                 = var.env
  inegi_api_key_value = var.inegi_api_key_value
}

# ---------------------------------------------------------------------
# MÓDULO DE FUNCIONES SERVERLESS (LAMBDA)
# Las 6 funciones del backend + Lambda Layer compartida.
# Registra las rutas en API Gateway y conecta con DynamoDB/Bedrock.
# Depende de: dynamodb, api_gateway, ssm, iam
# ---------------------------------------------------------------------
module "lambda" {
  source       = "./modules/lambda"
  project_name = var.project_name
  env          = var.env
  aws_region   = var.aws_region

  lambda_role_arn       = aws_iam_role.lambda_exec.arn
  api_id                = module.api_gateway.api_id
  authorizer_id         = module.api_gateway.authorizer_id
  bedrock_model_id      = var.bedrock_model_id
  lambda_code_base_path = var.lambda_code_base_path

  users_table_name        = module.dynamodb.users_table_name
  transactions_table_name = module.dynamodb.transactions_table_name
  alerts_table_name       = module.dynamodb.alerts_table_name

  ssm_inegi_key_arn = module.ssm.inegi_api_key_arn
  pandas_layer_arn  = var.pandas_layer_arn
}

# ---------------------------------------------------------------------
# MÓDULO DE ANALÍTICA (ATHENA)
# Configura Glue Catalog y Athena Database para el Data Lake.
# ---------------------------------------------------------------------
module "athena" {
  source                = "./modules/athena"
  project_name          = var.project_name
  env                   = var.env
  athena_results_bucket = module.s3.athena_results_bucket_name
  datalake_bucket       = module.s3.datalake_bucket_name
}


# ---------------------------------------------------------------------
# MÓDULO DE TAREAS PROGRAMADAS (EVENTBRIDGE)
# Dispara analyze_expenses automáticamente cada lunes a las 9am UTC.
# Depende de: lambda
# ---------------------------------------------------------------------
module "eventbridge" {
  source       = "./modules/eventbridge"
  project_name = var.project_name
  env          = var.env

  analyze_expenses_function_arn  = module.lambda.analyze_expenses_function_arn
  analyze_expenses_function_name = module.lambda.analyze_expenses_function_name

  # Pipeline IA: ForecastReady → get_ai_advice
  get_ai_advice_function_arn  = module.lambda.get_ai_advice_function_arn
  get_ai_advice_function_name = module.lambda.get_ai_advice_function_name

  # Pipeline IA: DataIngested → get_forecast
  get_forecast_function_arn  = module.lambda.get_forecast_function_arn
  get_forecast_function_name = module.lambda.get_forecast_function_name
}

