model_package_group           = "FraudDetectionXGBGroup"
github_owner                  = "GoormCloud-3"
github_repo                   = "FinGuard-Flask"
github_pat_secret_name         = "github-pat-token-finguard-0i1xNK"
sagemaker_processing_role_name = "finguard-pipeline-exec-role"
monitor_image_uri             = "709848358524.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-model-monitor-analyzer:latest"
enable_monitor_envs = ["prod"]
