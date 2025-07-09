variable "aws_region" {
  default = "ap-northeast-2"
  description = "AWS region"
}

variable "s3_fraud_name" {
  type = string
  description = "S3 bucket storing the model artifact"
}

variable "s3_fraud_prefix" {
  type = string
  description = "Path to model artifact folder"
}

variable "ecr_repository_name" {
  type = string
  description = "ECR repo name"
}

variable "ecr_image_tag_or_digest" {
  type = string
  description = "ECR image tag (e.g., 'latest') or digest (e.g., '@sha256:...')"
}

variable "fraud_model_file_name"{
  default = "model.tar.gz"
  description = "name of model artifact file"
}

variable "sagemaker_model_name"{
  default = "fraud-detector"
}

variable "endpoint_config_name"{
  default = "fraud-endpoint-config"
}

variable "endpoint_name"{
  default = "fraud-endpoint"
}
