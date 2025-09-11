data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { 
      type = "Service" 
      identifiers = ["lambda.amazonaws.com"] 
    }
  }
}

# build handler.py to zip
data "archive_file" "gh_dispatch" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/gh_dispatch.zip"
}

resource "aws_iam_role" "lambda" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy" "policy" {
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect="Allow", Action=["secretsmanager:GetSecretValue"], Resource=[var.github_secret_arn] },
      { Effect="Allow", Action=[
          "logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"
        ], Resource="*" }
    ]
  })
}

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda.arn
  timeout       = 30

  filename         = data.archive_file.gh_dispatch.output_path
  source_code_hash = data.archive_file.gh_dispatch.output_base64sha256

  environment {
    variables = {
      GITHUB_OWNER      = var.github_owner
      GITHUB_REPO       = var.github_repo
      GITHUB_SECRET_ARN = var.github_secret_arn
      EVENT_TYPE        = var.event_type
    }
  }
}

# Model Package Approved 이벤트
resource "aws_cloudwatch_event_rule" "approved" {
  name = "${var.function_name}-on-approved"
  event_pattern = jsonencode({
    "source": ["aws.sagemaker"],
    "detail-type": ["SageMaker Model Package State Change"],
    "detail": {
      "ModelPackageGroupName": [var.model_package_group],
      "ModelApprovalStatus": ["Approved"]
    }
  })
}

resource "aws_cloudwatch_event_target" "to_lambda" {
  rule      = aws_cloudwatch_event_rule.approved.name
  target_id = "gh-sm-dispatch"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "events" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.approved.arn
}

