resource "aws_iam_policy" "sm_passrole_job" {
  name   = "finguard-sagemaker-passrole-job"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect: "Allow",
      Action: ["iam:PassRole"],
      Resource: aws_iam_role.sagemaker_job_role.arn,
      Condition: { StringEquals: { "iam:PassedToService": "sagemaker.amazonaws.com" } }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_sm_passrole_job" {
  role       = aws_iam_role.sagemaker_pipeline_role.name
  policy_arn = aws_iam_policy.sm_passrole_job.arn
}
