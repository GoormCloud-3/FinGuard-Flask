locals {
  envs = {
    staging = {
      endpoint_name      = "finguard-fraud-endpiont-staging"
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
}

