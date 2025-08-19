resource "aws_iam_role" "sagemaker_job_role" {
	name = "finguard-sagemaker-job-role"

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

resource "aws_iam_policy" "sagemaker_job_policy" {
	name = "sagemaker-job-policy"

	policy = jsonencode({
		Version = "2012-10-17",
		Statement = [
		{
			Effect="Allow",
			Action= [
				"s3:GetObject",
				"s3:ListBucket",
				"s3:PutObject"
			],
			Resource = [
				"arn:aws:s3:::finguard-model-artifacts",
				"arn:aws:s3:::finguard-model-artifacts/*"
			]
		},
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
        		Action = ["ecr:GetAuthorizationToken"],
        		Resource = "*"
       		},
		{
			Effect= "Allow",
			Action = [
				"ecr:BatchGetImage",
         	 		"ecr:GetDownloadUrlForLayer",
          			"ecr:BatchCheckLayerAvailability"
			],
			Resource: "arn:aws:ecr:${var.region}:${var.aws_account_id}:repository/*"
		}
		]
	})
}

resource "aws_iam_role_policy_attachment" "attach_job_policy" {
  role       = aws_iam_role.sagemaker_job_role.name
  policy_arn = aws_iam_policy.sagemaker_job_policy.arn
}

output "sagemaker_job_role_arn" {
  value = aws_iam_role.sagemaker_job_role.arn
}

output "sagemaker_job_role_name" {
  value = aws_iam_role.sagemaker_job_role.name
}
