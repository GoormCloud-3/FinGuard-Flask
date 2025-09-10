variable "endpoint_name"          { type = string }
variable "capture_s3_prefix"      { type = string }  # datacapture/<env>/
variable "reports_s3_prefix"      { type = string }  # monitor-reports/<env>/
variable "baseline_s3_prefix"     { type = string }  # monitor-baseline/<env>/
variable "exec_role_arn"          { type = string }  # for Processing (model monitor)
variable "instance_type"          { type = string  default = "ml.m5.xlarge" }
variable "instance_count"         { type = number  default = 1 }
variable "schedule_expression"    { type = string  default = "cron(0 * * * ? *)" } # per hour
variable "monitor_image_uri"      { type = string }  # region별 Model Monitor 이미지 URI
# ---- ModelQuality Option (if label exists) ----
variable "enable_model_quality"   { type = bool     default = false }
variable "ground_truth_s3_prefix" { type = string   default = "" }  # label site
variable "problem_type"           { type = string   default = "BinaryClassification" } # or Multiclass, Regression

