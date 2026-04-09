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

# Desbloquear acceso público (Necesario para hosting estático)
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Política de acceso público de lectura
resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      },
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
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

