data "aws_caller_identity" "current" {}

locals{
  aws_account_id = data.aws_caller_identity.current.account_id
  pipeline_def_json_root = (
    length(trimspace(var.pipeline_definition_path)) > 0 && fileexists(var.pipeline_definition_path)
  ) ? file(var.pipeline_definition_path) : "{}"
}
