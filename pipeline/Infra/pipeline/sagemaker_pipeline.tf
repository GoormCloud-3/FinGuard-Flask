locals {
  has_def           = var.pipeline_definition_json != null && length(trimspace(var.pipeline_definition_json)) > 0
  pipeline_def_json = local.has_def ? var.pipeline_definition_json : "{}"
}

resource "aws_sagemaker_pipeline" "fraud_pipenline" {
	pipeline_name = "FraudDetectionPipeline"
	pipeline_display_name = "Fraud-Detection-Pipeline"
	role_arn = var.sagemaker_role_arn
	pipeline_definition   = local.pipeline_def_json 
	tags={
		project = "fraud-detecion"
	}
}

