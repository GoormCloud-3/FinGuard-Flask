resource "aws_iam_role" "sagemaker_pipeline_role" {
	name = "finguard-sagemaker-pipeline-role"

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

resource "aws_iam_policy" "sagemaker_pipeline_policy" {
	name = "sagemaker-pipeline-policy"

	policy = jsonencode({
		Version = "2012-10-17",
		Statement = [
		{
			Effect = "Allow",
       	 		Action = [
          			"logs:CreateLogGroup",
          			"logs:CreateLogStream",
          			"logs:PutLogEvents"
        			],
        		Resource = "*"
		},
		{
       	 		Effect = "Allow",
        		Action = ["sagemaker:*"],
        		Resource = "*"
       		},
		{
			Effect = "Allow",
			Action   = ["s3:ListBucket"],
        		Resource = "arn:aws:s3:::finguard-model-artifacts"
		},
		{
			Effect = "Allow",
			Action = ["s3:GetObject", "s3:PutObject"],
			Resource = "arn:aws:s3:::finguard-model-artifacts/*"
		},
		{
			Effect = "Allow",
        		Action = ["ecr:GetAuthorizationToken"],
        		Resource = "*"
		},
		{
			Effect = "Allow",
        		Action = [
          			"ecr:BatchGetImage",
          			"ecr:GetDownloadUrlForLayer",
          			"ecr:BatchCheckLayerAvailability",
          			"ecr:DescribeImages"
        		],
        		Resource = "arn:aws:ecr:${var.region}:${var.aws_account_id}:repository/finguard/pipeline-serving"
		}
		]
	})
}
resource "aws_iam_role_policy_attachment" "attach_sagemaker_pipeline_policy" {
  role       = aws_iam_role.sagemaker_pipeline_role.name
  policy_arn = aws_iam_policy.sagemaker_pipeline_policy.arn
}

output "sagemaker_pipeline_role_arn" {
  value = aws_iam_role.sagemaker_pipeline_role.arn
}

output "sagemaker_pipeline_role_name" {
  value = aws_iam_role.sagemaker_pipeline_role.name
}
