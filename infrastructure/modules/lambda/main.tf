# =====================================================================
# FUNCIONES SERVERLESS (LAMBDA)
# Las 6 funciones del backend de Incomia + la Lambda Layer compartida.
# Cada función tiene sus rutas en API Gateway y sus permisos de invocación.
# =====================================================================

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------
# LAMBDA LAYER COMPARTIDA (shared/)
# Contiene los módulos de DynamoDB y Bedrock que usan todas las funciones.
# ---------------------------------------------------------------------
resource "null_resource" "build_shared_layer" {
  triggers = {
    # Checksum of the shared directory to trigger rebuilds
    dir_sha = sha1(join("", [for f in fileset("${path.module}/${var.lambda_code_base_path}/shared", "**"): filesha1("${path.module}/${var.lambda_code_base_path}/shared/${f}")]))
  }

  provisioner "local-exec" {
    command = "${path.module}/build_layer.sh ${path.module}/${var.lambda_code_base_path}/shared ${path.module}/dist/layer_shared.zip"
  }
}

data "local_file" "layer_shared_zip" {
  filename   = "${path.module}/dist/layer_shared.zip"
  depends_on = [null_resource.build_shared_layer]
}

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${var.project_name}-shared"
  description         = "Módulos compartidos de DynamoDB y Bedrock para Incomia"
  filename            = data.local_file.layer_shared_zip.filename
  source_code_hash    = data.local_file.layer_shared_zip.content_base64sha256
  compatible_runtimes = ["python3.11"]
  depends_on          = [null_resource.build_shared_layer]
}

# ─────────────────────────────────────────────────────────────────────
# EMPAQUETADO DE CÓDIGO (archive_file por función)
# ─────────────────────────────────────────────────────────────────────

data "archive_file" "create_user" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/create_user"
  output_path = "${path.module}/dist/create_user.zip"
}

data "archive_file" "log_income" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/log_income"
  output_path = "${path.module}/dist/log_income.zip"
}

data "archive_file" "log_expense" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/log_expense"
  output_path = "${path.module}/dist/log_expense.zip"
}

data "archive_file" "data_generator" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/data_generator"
  output_path = "${path.module}/dist/data_generator.zip"
}

data "archive_file" "get_dashboard" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/get_dashboard"
  output_path = "${path.module}/dist/get_dashboard.zip"
}

data "archive_file" "update_user_config" {
  type        = "zip"
  source_dir  = "${path.module}/${var.lambda_code_base_path}/lambdas/update_user_config"
  output_path = "${path.module}/dist/update_user_config.zip"
}


data "archive_file" "analyze_expenses" {
  type        = "zip"
  output_path = "${path.module}/dist/analyze_expenses.zip"

  source {
    content  = file("${path.module}/${var.lambda_code_base_path}/lambdas/analyze_expenses/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${path.module}/../../../AI/weekly_alerts.py")
    filename = "weekly_alerts.py"
  }
}

data "archive_file" "inflation_alert" {
  type        = "zip"
  output_path = "${path.module}/dist/inflation_alert.zip"

  source {
    content  = file("${path.module}/${var.lambda_code_base_path}/lambdas/inflation_alert/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${path.module}/../../../AI/inflation_engine.py")
    filename = "inflation_engine.py"
  }
}

# get_forecast: handler.py + liquidity_forecast.py (bundled desde AI/)
# Usamos bloques `source` para incluir archivos de distintos directorios
data "archive_file" "get_forecast" {
  type        = "zip"
  output_path = "${path.module}/dist/get_forecast.zip"

  source {
    content  = file("${path.module}/${var.lambda_code_base_path}/lambdas/get_forecast/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${path.module}/../../../AI/liquidity_forecast.py")
    filename = "liquidity_forecast.py"
  }
}

# get_ai_advice: handler.py + advice_generator.py + liquidity_forecast.py
data "archive_file" "get_ai_advice" {
  type        = "zip"
  output_path = "${path.module}/dist/get_ai_advice.zip"

  source {
    content  = file("${path.module}/${var.lambda_code_base_path}/lambdas/get_ai_advice/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${path.module}/../../../AI/advice_generator.py")
    filename = "advice_generator.py"
  }

  source {
    content  = file("${path.module}/../../../AI/liquidity_forecast.py")
    filename = "liquidity_forecast.py"
  }
}

# ─────────────────────────────────────────────────────────────────────
# VARIABLES DE ENTORNO COMUNES A TODAS LAS FUNCIONES
# ─────────────────────────────────────────────────────────────────────

locals {
  common_env_vars = {
    USERS_TABLE        = var.users_table_name
    TRANSACTIONS_TABLE = var.transactions_table_name
    ALERTS_TABLE       = var.alerts_table_name
    BEDROCK_MODEL_ID   = var.bedrock_model_id
    AWS_REGION_NAME    = var.aws_region
  }
}

# =====================================================================
# LAMBDA 1: create_user — POST /users
# Crea un nuevo usuario en la tabla de DynamoDB.
# =====================================================================
resource "aws_lambda_function" "create_user" {
  function_name    = "${var.project_name}-create-user-${var.env}"
  filename         = data.archive_file.create_user.output_path
  source_code_hash = data.archive_file.create_user.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "create_user" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.create_user.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_user" {
  api_id             = var.api_id
  route_key          = "POST /users"
  target             = "integrations/${aws_apigatewayv2_integration.create_user.id}"
  authorization_type = "NONE" # Creación de usuario es pública (registro)
}

resource "aws_lambda_permission" "create_user" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users"
}

# =====================================================================
# LAMBDA 2: log_income — POST /users/{userId}/income
# Registra un ingreso y recalcula el sueldo simulado del usuario.
# =====================================================================
resource "aws_lambda_function" "log_income" {
  function_name    = "${var.project_name}-log-income-${var.env}"
  filename         = data.archive_file.log_income.output_path
  source_code_hash = data.archive_file.log_income.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "log_income" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.log_income.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "log_income" {
  api_id             = var.api_id
  route_key          = "POST /users/{userId}/income"
  target             = "integrations/${aws_apigatewayv2_integration.log_income.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "log_income" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_income.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/income"
}

# =====================================================================
# LAMBDA 3: log_expense — POST /users/{userId}/expense
# Registra y clasifica un gasto con Amazon Bedrock (IA).
# =====================================================================
resource "aws_lambda_function" "log_expense" {
  function_name    = "${var.project_name}-log-expense-${var.env}"
  filename         = data.archive_file.log_expense.output_path
  source_code_hash = data.archive_file.log_expense.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "log_expense" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.log_expense.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "log_expense" {
  api_id             = var.api_id
  route_key          = "POST /users/{userId}/expense"
  target             = "integrations/${aws_apigatewayv2_integration.log_expense.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "log_expense" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_expense.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/expense"
}

# =====================================================================
# LAMBDA 4: get_dashboard — GET /users/{userId}/dashboard
# Retorna el resumen financiero del usuario (sólo lectura).
# =====================================================================
resource "aws_lambda_function" "get_dashboard" {
  function_name    = "${var.project_name}-get-dashboard-${var.env}"
  filename         = data.archive_file.get_dashboard.output_path
  source_code_hash = data.archive_file.get_dashboard.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "get_dashboard" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_dashboard.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_dashboard" {
  api_id             = var.api_id
  route_key          = "GET /users/{userId}/dashboard"
  target             = "integrations/${aws_apigatewayv2_integration.get_dashboard.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "get_dashboard" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_dashboard.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/dashboard"
}

# =====================================================================
# LAMBDA EXTRA: update_user_config — PATCH /users/{userId}
# Actualiza sueldo y modo del usuario.
# =====================================================================
resource "aws_lambda_function" "update_user_config" {
  function_name    = "${var.project_name}-update-user-config-${var.env}"
  filename         = data.archive_file.update_user_config.output_path
  source_code_hash = data.archive_file.update_user_config.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }
}

resource "aws_apigatewayv2_integration" "update_user_config" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.update_user_config.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "update_user_config" {
  api_id             = var.api_id
  route_key          = "PATCH /users/{userId}"
  target             = "integrations/${aws_apigatewayv2_integration.update_user_config.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "update_user_config" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_user_config.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*"
}


# =====================================================================
# LAMBDA 5: analyze_expenses — POST /users/{userId}/analyze
# Analiza patrones de gasto con Bedrock y genera alertas inteligentes.
# Timeout extendido a 60s por la llamada a Bedrock.
# También se dispara via EventBridge cada lunes a las 9am UTC.
# =====================================================================
resource "aws_lambda_function" "analyze_expenses" {
  function_name    = "${var.project_name}-analyze-expenses-${var.env}"
  filename         = data.archive_file.analyze_expenses.output_path
  source_code_hash = data.archive_file.analyze_expenses.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60 # Extendido para acomodar llamadas a Bedrock
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = local.common_env_vars
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "analyze_expenses" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.analyze_expenses.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "analyze_expenses" {
  api_id             = var.api_id
  route_key          = "POST /users/{userId}/analyze"
  target             = "integrations/${aws_apigatewayv2_integration.analyze_expenses.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "analyze_expenses_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analyze_expenses.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/analyze"
}

# =====================================================================
# LAMBDA 6: inflation_alert — GET /users/{userId}/inflation
# Calcula inflación personalizada con datos de INEGI y genera alertas.
# Requiere permiso de lectura al parámetro SSM de INEGI.
# =====================================================================
resource "aws_lambda_function" "inflation_alert" {
  function_name    = "${var.project_name}-inflation-alert-${var.env}"
  filename         = data.archive_file.inflation_alert.output_path
  source_code_hash = data.archive_file.inflation_alert.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  role             = var.lambda_role_arn
  layers           = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = merge(local.common_env_vars, {
      INEGI_API_KEY_PARAM = "/incomia/inegi_api_key"
    })
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "inflation_alert" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.inflation_alert.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "inflation_alert" {
  api_id             = var.api_id
  route_key          = "GET /users/{userId}/inflation"
  target             = "integrations/${aws_apigatewayv2_integration.inflation_alert.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "inflation_alert" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inflation_alert.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/inflation"
}

# =====================================================================
# LAMBDA 7: get_forecast — GET /users/{userId}/ai/forecast
# Pronostica liquidez a 14 días con Prophet o Moving Average.
# Usa numpy — requiere la capa de numpy/pandas (var.pandas_layer_arn).
# También emite evento ForecastReady a EventBridge.
# Timeout extendido a 90s: Prophet puede tardar en entornos fríos.
# =====================================================================
resource "aws_lambda_function" "get_forecast" {
  function_name    = "${var.project_name}-get-forecast-${var.env}"
  filename         = data.archive_file.get_forecast.output_path
  source_code_hash = data.archive_file.get_forecast.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 90
  memory_size      = 512
  role             = var.lambda_role_arn
  layers           = compact([
    aws_lambda_layer_version.shared.arn,
    var.pandas_layer_arn,
  ])

  environment {
    variables = merge(local.common_env_vars, {
      EVENTBRIDGE_BUS_NAME = "${var.project_name}-events-${var.env}"
    })
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "get_forecast" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_forecast.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_forecast" {
  api_id             = var.api_id
  route_key          = "GET /users/{userId}/ai/forecast"
  target             = "integrations/${aws_apigatewayv2_integration.get_forecast.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "get_forecast" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_forecast.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/ai/forecast"
}

# =====================================================================
# LAMBDA 8: get_ai_advice — GET /users/{userId}/ai/advice
# Genera consejo financiero personalizado con Amazon Bedrock Nova Pro.
# También se dispara vía EventBridge ForecastReady (pipeline IA).
# Timeout extendido a 90s para acomodar la llamada a Bedrock.
# =====================================================================
resource "aws_lambda_function" "get_ai_advice" {
  function_name    = "${var.project_name}-get-ai-advice-${var.env}"
  filename         = data.archive_file.get_ai_advice.output_path
  source_code_hash = data.archive_file.get_ai_advice.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 90
  memory_size      = 512
  role             = var.lambda_role_arn
  layers           = compact([
    aws_lambda_layer_version.shared.arn,
    var.pandas_layer_arn,
  ])

  environment {
    variables = merge(local.common_env_vars, {
      EVENTBRIDGE_BUS_NAME = "${var.project_name}-events-${var.env}"
    })
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_apigatewayv2_integration" "get_ai_advice" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_ai_advice.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_ai_advice" {
  api_id             = var.api_id
  route_key          = "GET /users/{userId}/ai/advice"
  target             = "integrations/${aws_apigatewayv2_integration.get_ai_advice.id}"
  authorization_type = "JWT"
  authorizer_id      = var.authorizer_id
}

resource "aws_lambda_permission" "get_ai_advice_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_ai_advice.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.api_id}/*/*/users/*/ai/advice"
}

# Permite que EventBridge invoque get_ai_advice (pipeline ForecastReady)
resource "aws_lambda_permission" "get_ai_advice_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_ai_advice.function_name
  principal     = "events.amazonaws.com"
  source_arn    = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/${var.project_name}-events-${var.env}/*"
}

# ---------------------------------------------------------------------
# LAMBDA 9: data_generator — Ingestión de Datos Sintéticos
# Genera datos y los inyecta a DynamoDB/S3 para inicializar el lake.
# =====================================================================
resource "aws_lambda_function" "data_generator" {
  function_name    = "${var.project_name}-data-generator-${var.env}"
  filename         = data.archive_file.data_generator.output_path
  source_code_hash = data.archive_file.data_generator.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 120
  memory_size      = 512
  role             = var.lambda_role_arn
  layers           = compact([
    aws_lambda_layer_version.shared.arn,
    var.pandas_layer_arn,
  ])

  environment {
    variables = merge(local.common_env_vars, {
      EVENTBRIDGE_BUS_NAME        = "${var.project_name}-events-${var.env}"
      S3_BUCKET                   = "incomia-datalake-${var.env}"
      DYNAMODB_TABLE_USERS        = "${var.project_name}-users-${var.env}"
      DYNAMODB_TABLE_TRANSACTIONS = "${var.project_name}-transactions-${var.env}"
      DYNAMODB_TABLE_EXPENSES     = "${var.project_name}-alerts-${var.env}" # En el generador se usa para una tabla de gastos, pero lo mapearemos a alerts para el demo o similar
    })
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}


output "data_generator_function_arn" {
  value = aws_lambda_function.data_generator.arn
}

output "data_generator_function_name" {
  value = aws_lambda_function.data_generator.function_name
}

