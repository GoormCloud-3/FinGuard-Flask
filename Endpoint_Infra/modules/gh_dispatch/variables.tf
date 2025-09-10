variable "model_package_group" { 
  type = string 
}
variable "github_owner" { 
  type = string 
}
variable "github_repo"  { 
  type = string 
}
variable "github_secret_arn" { 
  type = string
}              # Secrets Manager ARN (PAT or App token)
variable "function_name" {  
  type = string  
  default = "gh-sm-dispatch-on-approve"
}
variable "event_type" { 
  type = string  
  default = "model-approved" 
}

