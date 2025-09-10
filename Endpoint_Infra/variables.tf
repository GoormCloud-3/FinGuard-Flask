variable "model_package_group" { type = string }
variable "github_owner"        { type = string }
variable "github_repo"         { type = string }
variable "github_pat_secret_arn" { type = string }
variable "ops_sns_topic_arn"   { type = string  default = null } 
variable "sagemaker_processing_role_arn" { type = string }
variable "monitor_image_uri"             { type = string } # 예:  <acct>.dkr.ecr.<region>.amazonaws.com/sagemaker-model-monitor-analyzer

