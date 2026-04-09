# =====================================================================
# ALMACENAMIENTO DE OBJETOS: FRONTEND & DATA LAKE
# S3 guarda los bits, ya sean páginas web estáticas HTML o
# archivos de analítica pura (Logs, Imágenes, etc.)
# =====================================================================

# 1. BUCKET DEL FRONTEND -> Hospeda a React
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend-${var.env}"

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# Configuración del bucket frontend para funcionar como servidor web estático.
# Todas las rutas buscarán index.html (esto favorece a la navegación de React - SPA).
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  index_document { suffix = "index.html" }
  error_document  { key    = "index.html" }
}

# ---------------------------------------------------------------------

# 2. BUCKET DEL DATA LAKE -> Hospeda nuestra información asíncrona / documentos IA
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-datalake-${var.env}"

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

# Activación del control de versiones. 
# Si alguien sobrescribe o elimina un reporte, podremos revertirlo, protegiendo 
# nuestros datos crudos más valiosos del sistema.
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration { status = "Enabled" }
}

# 3. BUCKET DE RESULTADOS ATHENA -> Guarda los resultados de las consultas SQL
resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.project_name}-athena-results-${var.env}"

  tags = {
    Project     = var.project_name
    Environment = var.env
  }
}

