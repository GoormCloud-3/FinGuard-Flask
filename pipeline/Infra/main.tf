provider "aws" {
	region = var.aws_region
}

module "iam" {
	source = "./iam"
	region = var.aws_region
	aws_account_id = local.aws_account_id
}

module "lambda" {
	source = "./lambda"
}

module "pipeline" {
	source = "./pipeline"
	sagemaker_role_arn = module.iam.sagemaker_pipeline_role_arn
	pipeline_definition_json = var.pipeline_definition_json
	depends_on = [
		module.iam, 
		module.lambda,
		aws_iam_role_policy_attachment.attach_sm_invoke_lambda
	]
}
