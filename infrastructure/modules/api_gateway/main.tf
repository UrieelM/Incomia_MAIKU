# =====================================================================
# APERTURA AL EXTERIOR Y ENRUTAMIENTO (API GATEWAY)
# Aquí nacen los endpoints de bajo costo (API HTTP). Todo nuestro Backend "Lambda"
# responderá detrás de estas paredes transparentes y protegidas.
# =====================================================================

# 1. DECLARACIÓN DEL API
# Una API HTTP configurada para ser simple y barata y conectar a los Lambdas.
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  # Apertura general segura de CORS, vital si el frontend está alojado en otro
  # dominio (Ej. S3 Website u otro entorno). Sin esto el navegador bloquearía consultas.
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }

  tags = {
    Project = var.project_name
  }
}

# 2. EL ESCUDO DE PROTECCIÓN OBLIGATORIO (AUTHORIZER)
# Integramos la ruta HTTP con Amazon Cognito. 
# Si el header "Authorization" viaja sin token, API gateway devuelve error 401 
# antes si quiera de molestar o despertar nuestras funciones Lambda.
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  
  # Validaremos el token donde llegue bajo este Header standard HTTP
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.project_name}-cognito-auth"

  # Las banderas del validador: Apuntamos exactamente a nuestra piscina de usuarios ("User Pool") 
  # creada en la región actual para verificar la legitimidad del JWT emitido.
  jwt_configuration {
    audience = [var.cognito_client_id]
    issuer   = "https://cognito-idp.${var.region}.amazonaws.com/${var.cognito_pool_id}"
  }
}

# 3. ENTORNO DE DESPLIEGUE (STAGE DE DEFAULT)
# Permite que la configuración anterior y cualquier ruta adherida hagan flush 
# directo al servidor y se asignen a un enlace web vivo instantáneamente.
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}
