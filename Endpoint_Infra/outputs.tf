output "alarm_5xx_names" {
  value = { for k, m in module.endpoint_alarms : k => m.alarm_5xx_name }
}
output "alarm_latency_p95_names" {
  value = { for k, m in module.endpoint_alarms : k => m.alarm_latency_p95_name }
}

