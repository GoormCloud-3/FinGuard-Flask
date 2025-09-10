resource "aws_sagemaker_pipeline" "fraud_pipenline" {
	pipeline_name = "FraudDetectionPipeline"
	pipeline_display_name = "Fraud-Detection-Pipeline"
	role_arn = var.sagemaker_role_arn
	pipeline_definition   = var.pipeline_definition_json
	tags={
		project = "fraud-detecion"
	}
}

