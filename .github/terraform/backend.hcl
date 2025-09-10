bucket         = "finguard-model-artifacts"
region         = "ap-northeast-2"
dynamodb_table = "terraform-lock"
key            = "sagemaker-pipeline/infra.tfstate"
workspace_key_prefix = "env"

