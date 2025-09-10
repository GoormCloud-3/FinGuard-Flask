variable "sagemaker_role_arn" {
  description = "IAM role ARN for SageMaker"
}

variable "pipeline_definition_json" {
  type = string
  default = null
}
