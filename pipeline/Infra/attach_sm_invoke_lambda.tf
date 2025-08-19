resource "aws_iam_policy" "sm_invoke_lambda" {
  name = "sagemaker-invoke-prev-auc"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["lambda:InvokeFunction"],
      Resource = module.lambda.get_previous_auc_lambda_arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_sm_invoke_lambda" {
  role       = module.iam.sagemaker_pipeline_role_name
  policy_arn = aws_iam_policy.sm_invoke_lambda.arn
  depends_on = [module.lambda]
}
