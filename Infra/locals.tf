data "aws_caller_identity" "current" {}

locals{
  aws_account_id = data.aws_caller_identity.current.account_id
  s3_fraud_model_uri = "s3://${var.s3_fraud_name}/${var.s3_fraud_prefix}/${var.fraud_model_file_name}"
  ecr_image_uri = "${local.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository_name}"
  ecr_repository_arn = "arn:aws:ecr:${var.aws_region}:${local.aws_account_id}:repository/${var.ecr_repository_name}"
  s3_model_object_arn = "arn:aws:s3:::${var.s3_fraud_name}/${var.s3_fraud_prefix}/*"
  s3_bucket_arn = "arn:aws:s3:::${var.s3_fraud_name}"
}
