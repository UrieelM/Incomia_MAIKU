# =====================================================================
# BASE DE DATOS NOSQL: TABLAS PARA INFORMACIÓN ESTRUCTURADA
# DynamoDB es una BD sin servidor que ofrece una latencia rapidísima,
# la usaremos para los modelos críticos.
# =====================================================================

# TABLA DE USUARIOS -> Almacena la entidad base de clientes o usuarios
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users-${var.env}"
  # "PAY_PER_REQUEST" ajusta dinámicamente nuestra capacidad de lecturas
  # evitando que paguemos servidores dedicados no usados.
  billing_mode = "PAY_PER_REQUEST"
  
  # "userId" funcionará como nuestro identificador único (Hash Key)
  hash_key     = "userId"
  attribute {
    name = "userId"
    type = "S" # S = String
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# TABLA DE TRANSACCIONES -> Almacena movimientos o el log continuo del user
resource "aws_dynamodb_table" "transactions" {
  name      = "${var.project_name}-transactions-${var.env}"
  billing_mode = "PAY_PER_REQUEST"
  
  # Usamos una estructura jerárquica: Hash (ID User) + Range (Timestamp)
  # Así podemos buscar "todas las transacciones del Usuario X en la fecha Y"
  hash_key  = "userId"
  range_key = "timestamp"

  attribute {
    name = "userId"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}
