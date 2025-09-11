data "aws_caller_identity" "me" {}
data "aws_region" "cur" {}

locals {
  account_id = data.aws_caller_identity.me.account_id
  region     = data.aws_region.cur.name
  # Secrets Manager ARN (이름만 받아서 여기서 ARN 생성)
  github_pat_secret_arn = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:${var.github_pat_secret_name}"

  # Processing Role ARN (이름만 받아서 여기서 ARN 생성)
  sagemaker_processing_role_arn = "arn:aws:iam::${local.account_id}:role/${var.sagemaker_processing_role_name}"

  # Model Monitor Analyzer Image URI (리전만 반영)
  monitor_image_uri = "709848358524.dkr.ecr.${local.region}.amazonaws.com/sagemaker-model-monitor-analyzer:latest"

  envs = {
    staging = {
      endpoint_name      = "finguard-fraud-endpoint-staging"
      capture_s3_prefix  = "s3://finguard-model-artifacts/datacapture/staging/"
      reports_s3_prefix  = "s3://finguard-model-artifacts/monitor-reports/staging/"
      baseline_s3_prefix = "s3://finguard-model-artifacts/monitor-baseline/staging/"
      enable_mq          = false           # if not labeled data, false
      ground_truth_s3    = "" # path of label, if enable_mq = false -> ""
    }
    prod = {
      endpoint_name      = "finguard-fraud-endpoint-prod"
      capture_s3_prefix  = "s3://finguard-model-artifacts/datacapture/prod/"
      reports_s3_prefix  = "s3://finguard-model-artifacts/monitor-reports/prod/"
      baseline_s3_prefix = "s3://finguard-model-artifacts/monitor-baseline/prod/"
      enable_mq          = true            # if want to evaluate label, true
      ground_truth_s3    = "s3://finguard-model-artifacts/ground-truth/prod/" 
    }
  }

  monitor_envs = {
    for k, v in local.envs : k => v
    if contains(var.enable_monitor_envs, k)
  }

}

