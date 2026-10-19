output "cluster_name" {
  description = "Name of the ECS cluster."
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "Name of the ECS service (find its task's public IP in the console or with aws ecs describe-tasks)."
  value       = aws_ecs_service.api.name
}

output "log_group_name" {
  description = "CloudWatch log group of the API container."
  value       = aws_cloudwatch_log_group.api.name
}
