# =====================================================================
# BASE DE DATOS NOSQL: TABLAS PARA INFORMACIÓN ESTRUCTURADA
# DynamoDB es una BD sin servidor que ofrece una latencia rapidísima,
# la usaremos para los modelos críticos.
# =====================================================================

# TABLA DE USUARIOS → Almacena la entidad base de clientes o usuarios
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users-${var.env}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# TABLA DE TRANSACCIONES → Almacena el log continuo de ingresos y gastos del usuario.
# CLAVE: userId (hash) + transactionId (range) — alineado con el código Lambda en db.py.
# NOTA: Se corrigió conflicto previo donde Terraform usaba "timestamp" como range key
#       mientras el código Lambda usa "transactionId". Ahora ambos son consistentes.
resource "aws_dynamodb_table" "transactions" {
  name         = "${var.project_name}-transactions-${var.env}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "userId"
  range_key = "transactionId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "transactionId"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# TABLA DE ALERTAS → Almacena alertas de inflación y análisis de gastos por usuario.
# Necesaria para inflation_alert y analyze_expenses (faltaba en la definición original).
resource "aws_dynamodb_table" "alerts" {
  name         = "${var.project_name}-alerts-${var.env}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "userId"
  range_key = "alertId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "alertId"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}
