output "user_pool_id"     { value = aws_cognito_user_pool.main.id }
output "user_pool_client" { value = aws_cognito_user_pool_client.frontend.id }
