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

