# IAM role for fraud model (sagemaker)
resource "aws_iam_role" "fraud_model_role" {
	name = "fraud-model-role"
	
	assume_role_policy = jsonencode({
		Version = "2012-10-17",
		Statement = [{
			Effect = "Allow",
			Principal = {
				Service = "sagemaker.amazonaws.com"
			},
			Action = "sts:AssumeRole"
		}]
		
	})
}

#IAM policy for fraud model (s3)
resource "aws_iam_role_policy" "fraud_model_s3_policy" {
	name = "fraud-model-s3-access"
	role = aws_iam_role.fraud_model_role.id

	policy = jsonencode({
		Version = "2012-10-17",
		Statement = [{
			Sid = "AllowModelObjectRead",
			Effect = "Allow",
			Action = [
			"s3:GetObject",
			"s3:GetObjectVersion"
			],
			Resource = local.s3_model_object_arn},
			{
			Sid = "ListBucketForModel",
			Effect = "Allow",
			Action = [
			"s3:ListBucket"
			],
			Resource = local.s3_bucket_arn
			}]
	})
}

#IAM policy for fraud model (ecr)
resource "aws_iam_role_policy" "fraud_model_ecr_policy" {
  name = "fraud-model-ecr-access"
  role = aws_iam_role.fraud_model_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowGetAuthorizationToken",
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Resource = "*"
      },
      {
        Sid    = "AllowECRImagePull",
        Effect = "Allow",
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        Resource = local.ecr_repository_arn
      }
    ]
  })
}

#SageMaker Inference Model for Fraud Detector
resource "aws_sagemaker_model" "fraud_model" {
	name = var.sagemaker_model_name
	execution_role_arn = aws_iam_role.fraud_model_role.arn
	
	primary_container {
		image = local.ecr_image_uri
		model_data_url = local.s3_fraud_model_uri
		mode = "SingleModel"
	}
}

#SageMaker EndPoint Config for Fraud Detector
resource "aws_sagemaker_endpoint_configuration" "fraud_config" {
	name = var.endpoint_config_name
	production_variants {
		variant_name = "AllTraffic"
		model_name = aws_sagemaker_model.fraud_model.name
		serverless_config {
			memory_size_in_mb = 2048
			max_concurrency = 5
		}
	}

}

#SageMaker EndPoint for Fraud Detector
resource "aws_sagemaker_endpoint" "fraud_endpoint" {
	name = var.endpoint_name
	endpoint_config_name = aws_sagemaker_endpoint_configuration.fraud_config.name
}


