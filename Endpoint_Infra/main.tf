# Alarm
module "endpoint_alarms" {
  source   = "./modules/alarms"
  for_each = local.envs
  endpoint_name             = each.value.endpoint_name
  variant_name              = "AllTraffic"
  sns_topic_arn             = var.ops_sns_topic_arn
  latency_p95_threshold_ms  = 500
}

# EventBridge → GitHub Dispatch
module "gh_dispatch" {
  source               = "./modules/gh_dispatch"
  model_package_group  = var.model_package_group
  github_owner         = var.github_owner
  github_repo          = var.github_repo
  github_secret_arn    = local.github_pat_secret_arn

  function_name = "gh-sm-dispatch-on-approve-${terraform.workspace}"
}

# Model Monitor (Data/Model Quality)
module "endpoint_monitor" {
  source   = "./modules/monitor"
  for_each = local.monitor_envs

  endpoint_name          = each.value.endpoint_name
  capture_s3_prefix      = each.value.capture_s3_prefix
  reports_s3_prefix      = each.value.reports_s3_prefix
  baseline_s3_prefix     = each.value.baseline_s3_prefix

  exec_role_arn          = local.sagemaker_processing_role_arn       # ProcessingJob
  instance_type          = "ml.m5.xlarge"
  instance_count         = 1
  schedule_expression    = "cron(0 * * * ? *)"   # per an hour

  monitor_image_uri      = local.monitor_image_uri # Model Monitor image URI on region

  # enable_model_quality   = each.value.enable_mq
  # ground_truth_s3_prefix = each.value.ground_truth_s3
  # problem_type           = "BinaryClassification"
}
