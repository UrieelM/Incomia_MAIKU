# =====================================================================
# IDENTIDAD Y ACCESO PARA APLICACIONES MÓVILES Y WEB
# Amazon Cognito nos ahorra programar el registro, encriptación 
# de contraseñas y recuperación de cuentas.
# =====================================================================

# 1. COGNITO USER POOL -> El "Servidor/Directorio de Identidad"
# Centraliza toda la bóveda de usuarios, contraseñas y teléfonos.
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"

  # Regulamos la dureza de las credenciales
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
  }

  # Configura validación de pertenencia. Al registrarse, AWS enviará automáticamente 
  # un código de verificación al email para impedir bots o SPAM.
  auto_verified_attributes = ["email"]

  tags = {
    Project = var.project_name
  }
}

# 2. COGNITO APP CLIENT -> El "Punto de Acceso del Frontend"
# Es la librería u objeto con la cual interactúa el navegador (React).
resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${var.project_name}-frontend-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Habilitación de esquemas de autenticación estándar:
  # - Password_Auth: Logeo tradicional usuario+password
  # - Refresh_Token: Mantener la sesión activa rotando tokens detrás dev telón.
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
}
