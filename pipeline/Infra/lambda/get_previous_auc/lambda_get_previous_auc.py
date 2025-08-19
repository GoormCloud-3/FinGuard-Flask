import boto3
import json

def lambda_handler(event, context):
    sm = boto3.client("sagemaker")

    response = sm.list_model_packages(
        ModelPackageGroupName="FraudDetectionXGBGroup",
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1
    )

    if not response["ModelPackageSummaryList"]:
        return {"previous_auc": 0.0}

    model_package_arn = response["ModelPackageSummaryList"][0]["ModelPackageArn"]
    model_info = sm.describe_model_package(ModelPackageName=model_package_arn)
    metrics_json = model_info.get("ModelMetrics", {}).get("ModelStatistics", {}).get("Content", "")

    if not metrics_json:
        return {"previous_auc": 0.0}

    metrics = json.loads(metrics_json)
    auc = float(metrics["metrics"]["auc"])
    return {"previous_auc": auc}
