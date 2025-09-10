variable "endpoint_name" { type = string }
variable "variant_name"  { type = string  default = "AllTraffic" }
variable "sns_topic_arn" { type = string  default = null }
variable "latency_p95_threshold_ms" { type = number default = 500 }

