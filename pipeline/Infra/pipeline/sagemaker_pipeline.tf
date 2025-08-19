resource "aws_sagemaker_pipeline" "fraud_pipenline" {
	pipeline_name = "FraudDetectionPipeline"
	pipeline_display_name = "Fraud-Detection-Pipeline"
	role_arn = var.sagemaker_role_arn
	pipeline_definition = file(var.pipeline_definition_path)
	tags={
		project = "fraud-detecion"
	}
}

