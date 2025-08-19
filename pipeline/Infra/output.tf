output "sagemaker_pipeline_role_arn" {
  value = module.iam.sagemaker_pipeline_role_arn
}

output "get_previous_auc_lambda_arn" {
  value = module.lambda.get_previous_auc_lambda_arn
}

output "sagemaker_job_role_arn" {
  value = module.iam.sagemaker_job_role_arn
}
