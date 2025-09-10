resource "aws_cloudwatch_metric_alarm" "err5xx" {
  alarm_name          = "${var.endpoint_name}-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5XXError"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = var.variant_name
  }
  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  ok_actions    = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
}

resource "aws_cloudwatch_metric_alarm" "latency_p95" {
  alarm_name          = "${var.endpoint_name}-latency-p95"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = 60
  extended_statistic  = "p95"
  threshold           = var.latency_p95_threshold_ms
  treat_missing_data  = "notBreaching"
  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = var.variant_name
  }
  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  ok_actions    = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
}

