# =====================================================================
# PARÁMETROS SEGUROS (SSM PARAMETER STORE)
# Almacena secrets y configuraciones sensibles que las funciones Lambda
# leen en tiempo de ejecución (sin exponerlos en variables de entorno).
# =====================================================================

# ---------------------------------------------------------------------
# PARÁMETRO: API Key de INEGI
# Usada por inflation_alert para consultar datos de inflación oficiales
# de México. Se almacena como SecureString (cifrado con KMS).
# IMPORTANTE: El valor debe configurarse manualmente en la consola de AWS
# o via CLI después del primer 'terraform apply'.
# ---------------------------------------------------------------------
resource "aws_ssm_parameter" "inegi_api_key" {
  name        = "/incomia/inegi_api_key"
  description = "API Key para consumir los endpoints de INEGI (inflación México)"
  type        = "SecureString"

  # Valor placeholder — reemplázalo en la consola de AWS o con:
  # aws ssm put-parameter --name "/incomia/inegi_api_key" --value "TU_KEY" --type SecureString --overwrite
  value       = var.inegi_api_key_value

  lifecycle {
    # Evita que Terraform sobreescriba el valor si ya fue actualizado manualmente
    ignore_changes = [value]
  }

  tags = {
    Project     = var.project_name
    Environment = var.env
    ManagedBy   = "terraform"
  }
}
