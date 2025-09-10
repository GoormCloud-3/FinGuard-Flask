# (1) Data Quality Job Definition
resource "aws_sagemaker_data_quality_job_definition" "dq" {
  job_definition_name = "${var.endpoint_name}-dq-jobdef"
  data_quality_app_specification {
    image_uri = var.monitor_image_uri
  }
  data_quality_baseline_config {
    constraints_resource {
    s3_uri = "${replace(var.baseline_s3_prefix, "/$", "")}/dataquality/constraints.json"
    }
  statistics_resource {
    s3_uri = "${replace(var.baseline_s3_prefix, "/$", "")}/dataquality/statistics.json"
    }
  }
  data_quality_job_input {
    endpoint_input {
      endpoint_name   = var.endpoint_name
      local_path      = "/opt/ml/processing/input"
      s3_input_mode   = "File"
      probability_threshold_attribute = 0.0
      # dataset_format { json { line = true } }  # JSONLines 사용 시
    }
  }
  data_quality_job_output_config {
    monitoring_outputs {
      s3_output {
        local_path = "/opt/ml/processing/output"
        s3_uri     = "s3://${replace(var.reports_s3_prefix, "/$", "")}/dataquality/"
        s3_upload_mode = "EndOfJob"
      }
    }
  }
  job_resources {
    cluster_config {
      instance_count = var.instance_count
      instance_type  = var.instance_type
      volume_size_in_gb = 30
    }
  }
  role_arn = var.exec_role_arn
  stopping_condition { max_runtime_in_seconds = 3600 }
}

# (2) Data Quality Monitoring Schedule (캡처된 데이터 점검)
resource "aws_sagemaker_monitoring_schedule" "dq_schedule" {
  monitoring_schedule_name = "${var.endpoint_name}-dq-schedule"
  monitoring_schedule_config {
    schedule_config { schedule_expression = var.schedule_expression }
    monitoring_job_definition_name = aws_sagemaker_data_quality_job_definition.dq.job_definition_name
    monitoring_type = "DataQuality"
  }
}

# (3) Model Quality (라벨이 있고 평가 가능할 때만)
resource "aws_sagemaker_model_quality_job_definition" "mq" {
  count = var.enable_model_quality ? 1 : 0

  job_definition_name = "${var.endpoint_name}-mq-jobdef"
  model_quality_app_specification {
    image_uri = var.monitor_image_uri
    problem_type = var.problem_type  # BinaryClassification / MulticlassClassification / Regression
  }
  model_quality_job_input {
    endpoint_input {
      endpoint_name = var.endpoint_name
      local_path    = "/opt/ml/processing/input/endpoint"
      s3_input_mode = "File"
    }
    ground_truth_s3_input {
      s3_uri = var.ground_truth_s3_prefix
    }
  }
  model_quality_job_output_config {
    monitoring_outputs {
      s3_output {
        local_path     = "/opt/ml/processing/output"
        s3_uri         = "s3://${replace(var.reports_s3_prefix, "/$", "")}/modelquality/"
        s3_upload_mode = "EndOfJob"
      }
    }
  }
  job_resources {
    cluster_config {
      instance_count     = var.instance_count
      instance_type      = var.instance_type
      volume_size_in_gb  = 30
    }
  }
  role_arn = var.exec_role_arn
  stopping_condition { max_runtime_in_seconds = 3600 }
}

resource "aws_sagemaker_monitoring_schedule" "mq_schedule" {
  count = var.enable_model_quality ? 1 : 0

  monitoring_schedule_name = "${var.endpoint_name}-mq-schedule"
  monitoring_schedule_config {
    schedule_config { schedule_expression = var.schedule_expression }
    monitoring_job_definition_name = aws_sagemaker_model_quality_job_definition.mq[0].job_definition_name
    monitoring_type = "ModelQuality"
  }
}

