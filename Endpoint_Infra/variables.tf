variable "model_package_group" { 
  type = string 
}
variable "github_owner"        { 
  type = string 
}
variable "github_repo"         { 
  type = string 
}
variable "github_pat_secret_name" { 
  type = string 
}
variable "ops_sns_topic_arn"   { 
  type = string  
  default = null
} 
variable "sagemaker_processing_role_name" { 
  type = string 
}
variable "monitor_image_uri" { 
  type = string 
}
variable "enable_monitor_envs" {
  description = "모니터링(DataQuality)을 생성/유지할 환경 리스트 (예: [\"staging\"], [\"prod\"], [\"staging\",\"prod\"])"
  type        = list(string)
  default     = []  # 기본은 꺼둠
}


