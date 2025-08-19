resource "aws_iam_role" "lambda_role" {
	name = "getPreviousAUC-lambda-role"

	assume_role_policy = jsonencode({
		Version = "2012-10-17",
		Statement = [{
			Action = "sts:AssumeRole",
			Principal = {
				Service = "lambda.amazonaws.com"
			},
			Effect = "Allow",
		}]
	})
}

resource "aws_iam_policy" "lambda_policy" {
	name = "getPrevioudAUC-sagemaker-policy"
	description = "Allow Lambda to access SageMaker Model Registry"

	policy = jsonencode({
		Version = "2012-10-17",
		Statement = [{
			Effect = "Allow",
			Action = [
				"sagemaker:ListModelPackages",
				"sagemaker:DescribeModelPackage"
			],
			Resource="*"
		},
		{
			Effect = "Allow",
			Action = [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			Resource = "*"
		}
		]
	})
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file  = "${path.module}/get_previous_auc/lambda_get_previous_auc.py"
  output_path = "${path.module}/get_previous_auc.zip"
}

resource "aws_lambda_function" "get_previous_auc" {
  function_name = "get-previous-model-auc"
  handler       = "lambda_get_previous_auc.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_role.arn
  filename      = data.archive_file.lambda_zip.output_path
  timeout       = 10
  publish	= true
}

output "get_previous_auc_lambda_arn" {
	value = aws_lambda_function.get_previous_auc.arn
}
