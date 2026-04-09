# =====================================================================
# ANALÍTICA DE DATOS (ATHENA & GLUE)
# Permite realizar consultas SQL sobre los archivos JSON en S3.
# =====================================================================

# 1. BASE DE DATOS ATHENA (GLUE CATALOG)
resource "aws_glue_catalog_database" "incomia_analytics" {
  name = "incomia_analytics_${var.env}"
}

# 2. WORKGROUP DE ATHENA
# Configura dónde se guardan los resultados de las consultas.
resource "aws_athena_workgroup" "main" {
  name = "${var.project_name}-workgroup-${var.env}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.athena_results_bucket}/results/"
    }
  }
}

# 3. TABLA: Usuarios
resource "aws_glue_catalog_table" "users" {
  name          = "users"
  database_name = aws_glue_catalog_database.incomia_analytics.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "classification"      = "json"
    "has_encrypted_data"  = "false"
  }

  storage_descriptor {
    location      = "s3://${var.datalake_bucket}/raw/users/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "JsonSerDe"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "ignore.malformed.json" = "true"
      }
    }

    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "primary_sector"
      type = "string"
    }
    columns {
      name = "sub_sector"
      type = "string"
    }
    columns {
      name = "display_name"
      type = "string"
    }
    columns {
      name = "email_hash"
      type = "string"
    }
    columns {
      name = "phone_hash"
      type = "string"
    }
    columns {
      name = "artificial_salary"
      type = "double"
    }
    columns {
      name = "stabilization_fund_balance"
      type = "double"
    }
    columns {
      name = "resilience_goal_type"
      type = "string"
    }
    columns {
      name = "resilience_goal_target"
      type = "double"
    }
    columns {
      name = "current_risk_score"
      type = "int"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "profile_version"
      type = "string"
    }
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "city"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "int"
  }
  partition_keys {
    name = "day"
    type = "int"
  }
}

# 4. TABLA: Transacciones
resource "aws_glue_catalog_table" "transactions" {
  name          = "transactions"
  database_name = aws_glue_catalog_database.incomia_analytics.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL             = "TRUE"
    "classification"     = "json"
    "has_encrypted_data" = "false"
  }

  storage_descriptor {
    location      = "s3://${var.datalake_bucket}/raw/transactions/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "JsonSerDe"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "ignore.malformed.json" = "true"
      }
    }

    columns {
      name = "transaction_id"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "timestamp"
      type = "string"
    }
    columns {
      name = "amount"
      type = "double"
    }
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "type"
      type = "string"
    }
    columns {
      name = "income_source"
      type = "string"
    }
    columns {
      name = "payment_method"
      type = "string"
    }
    columns {
      name = "description"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "int"
  }
  partition_keys {
    name = "day"
    type = "int"
  }
}

# 5. TABLA: Gastos Fijos
resource "aws_glue_catalog_table" "expenses" {
  name          = "expenses"
  database_name = aws_glue_catalog_database.incomia_analytics.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL             = "TRUE"
    "classification"     = "json"
    "has_encrypted_data" = "false"
  }

  storage_descriptor {
    location      = "s3://${var.datalake_bucket}/raw/expenses/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "JsonSerDe"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "ignore.malformed.json" = "true"
      }
    }

    columns {
      name = "expense_id"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "name"
      type = "string"
    }
    columns {
      name = "amount"
      type = "double"
    }
    columns {
      name = "due_day_of_month"
      type = "int"
    }
    columns {
      name = "category"
      type = "string"
    }
    columns {
      name = "is_active"
      type = "boolean"
    }
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "created_at"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "int"
  }
  partition_keys {
    name = "day"
    type = "int"
  }
}

# 6. NAMED QUERIES (Ejemplos sugeridos en athena_setup.sql)
resource "aws_athena_named_query" "salary_by_sector" {
  name      = "SalarioPromedioPorSector"
  workgroup = aws_athena_workgroup.main.id
  database  = aws_glue_catalog_database.incomia_analytics.name
  query     = "SELECT primary_sector, AVG(artificial_salary) as avg_salary FROM users GROUP BY primary_sector;"
}
