variable "sagemaker_role_arn" {
  description = "IAM role ARN for SageMaker"
}

variable "pipeline_definition_path" {
  description = "Absolute path to pipeline_definition.json"
  type        = string
}
