variable "aws_region" {
  default = "ap-northeast-2"
  description = "AWS region"
}

variable "pipeline_definition_path" {
  type = string
  default = ""
}

variable "enable_pipeline" {
  type = bool
  default = false
}
