# =====================================================================
# TAREAS PROGRAMADAS Y PIPELINE DE IA (EVENTBRIDGE)
#
# Recursos:
#  1. Bus personalizado "incomia-events" — para eventos del pipeline IA
#  2. Regla scheduled: analyze_expenses cada lunes 9am UTC
#  3. Regla event:     ForecastReady → get_ai_advice (pipeline IA)
# =====================================================================

# ---------------------------------------------------------------------
# BUS PERSONALIZADO DE EVENTOS
# Aísla los eventos de Incomia del bus "default" de AWS.
# Los Lambdas publican aquí con source = "incomia.*"
# ---------------------------------------------------------------------
resource "aws_cloudwatch_event_bus" "incomia" {
  name = "${var.project_name}-events-${var.env}"

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# ---------------------------------------------------------------------
# REGLA 1: Análisis Semanal de Gastos (bus default)
# Dispara analyze_expenses cada lunes a las 9:00 AM UTC para procesar
# los patrones de gasto de todos los usuarios activos de la semana.
# ---------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "weekly_analysis" {
  name                = "${var.project_name}-weekly-analysis-${var.env}"
  description         = "Análisis semanal de gastos — se ejecuta cada lunes a las 9am UTC"
  schedule_expression = "cron(0 9 ? * MON *)"
  state               = "ENABLED"

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_cloudwatch_event_target" "weekly_analysis" {
  rule      = aws_cloudwatch_event_rule.weekly_analysis.name
  target_id = "AnalyzeExpensesLambda"
  arn       = var.analyze_expenses_function_arn
}

resource "aws_lambda_permission" "eventbridge_analyze_expenses" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.analyze_expenses_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_analysis.arn
}

# ---------------------------------------------------------------------
# REGLA 2: Pipeline IA — ForecastReady → get_ai_advice
# Cuando get_forecast publica ForecastReady en el bus incomia-events,
# esta regla dispara automáticamente get_ai_advice para generar
# el consejo personalizado en background.
# ---------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "forecast_ready" {
  name           = "${var.project_name}-forecast-ready-${var.env}"
  description    = "Pipeline IA: ForecastReady → get_ai_advice (consejo Bedrock)"
  event_bus_name = aws_cloudwatch_event_bus.incomia.name
  state          = "ENABLED"

  event_pattern = jsonencode({
    source      = ["incomia.liquidity-forecast"]
    "detail-type" = ["ForecastReady"]
  })

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_cloudwatch_event_target" "forecast_ready" {
  rule           = aws_cloudwatch_event_rule.forecast_ready.name
  event_bus_name = aws_cloudwatch_event_bus.incomia.name
  target_id      = "GetAIAdviceLambda"
  arn            = var.get_ai_advice_function_arn
}

resource "aws_lambda_permission" "eventbridge_get_ai_advice" {
  statement_id  = "AllowEventBridgeInvokeAIAdvice"
  action        = "lambda:InvokeFunction"
  function_name = var.get_ai_advice_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.forecast_ready.arn
}

# ---------------------------------------------------------------------
# REGLA 3: Pipeline IA — DataIngested → get_forecast
# Cuando data_generator publica DataIngested en el bus incomia-events,
# esta regla dispara automáticamente get_forecast para actualizar
# las proyecciones de liquidez de los usuarios afectados.
# ---------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "data_ingested" {
  name           = "${var.project_name}-data-ingested-${var.env}"
  description    = "Pipeline IA: DataIngested → get_forecast (Pronóstico Prophet)"
  event_bus_name = aws_cloudwatch_event_bus.incomia.name
  state          = "ENABLED"

  event_pattern = jsonencode({
    source      = ["incomia.data-generator"]
    "detail-type" = ["DataIngested"]
  })

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

resource "aws_cloudwatch_event_target" "data_ingested" {
  rule           = aws_cloudwatch_event_rule.data_ingested.name
  event_bus_name = aws_cloudwatch_event_bus.incomia.name
  target_id      = "GetForecastTarget"
  arn            = var.get_forecast_function_arn
}

resource "aws_lambda_permission" "eventbridge_get_forecast" {
  statement_id  = "AllowEventBridgeInvokeDataIngested"
  action        = "lambda:InvokeFunction"
  function_name = var.get_forecast_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.data_ingested.arn
}

