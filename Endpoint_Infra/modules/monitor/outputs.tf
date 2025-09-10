output "dq_schedule_name" { value = aws_sagemaker_monitoring_schedule.dq_schedule.monitoring_schedule_name }
output "mq_schedule_name" { value = try(aws_sagemaker_monitoring_schedule.mq_schedule[0].monitoring_schedule_name, null) }

