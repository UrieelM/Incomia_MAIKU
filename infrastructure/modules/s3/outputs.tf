output "frontend_bucket_name" {
  description = "Nombre del bucket del frontend"
  value       = aws_s3_bucket.frontend.id
}

output "datalake_bucket_name" {
  description = "Nombre del bucket del data lake"
  value       = aws_s3_bucket.data_lake.id
}
