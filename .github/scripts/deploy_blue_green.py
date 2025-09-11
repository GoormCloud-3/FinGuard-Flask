# .github/scripts/deploy_blue_green.py
import argparse, os, time, boto3
from urllib.parse import urlparse
from botocore.exceptions import ClientError

sm = boto3.client("sagemaker")
s3 = boto3.client("s3")

def _wait_endpoint(endpoint_name, status="InService", timeout=7200, poll=20):
    end = time.time() + timeout
    while time.time() < end:
        resp = sm.describe_endpoint(EndpointName=endpoint_name)
        st = resp["EndpointStatus"]
        if st == status:
            return
        if st in ("Failed", "OutOfService"):
            raise RuntimeError(f"Endpoint {endpoint_name} status={st}")
        time.sleep(poll)
    raise TimeoutError(f"Timeout: {endpoint_name} not {status}")

def _latest_model_tar(s3_prefix: str) -> str:
    """
    s3_prefix: e.g. s3://finguard-model-artifacts/models/staging/
    returns:   e.g. s3://finguard-model-artifacts/models/staging/2025-09-11-120455/model.tar.gz
    """
    u = urlparse(s3_prefix)
    if u.scheme != "s3" or not u.netloc:
        raise ValueError(f"Invalid S3 prefix: {s3_prefix}")
    bucket = u.netloc
    prefix = u.path.lstrip("/")
    # list & pick latest *.tar.gz
    paginator = s3.get_paginator("list_objects_v2")
    latest = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".tar.gz"):
                continue
            if (latest is None) or (obj["LastModified"] > latest["LastModified"]):
                latest = obj
    if not latest:
        raise FileNotFoundError(f"No *.tar.gz under {s3_prefix}")
    return f"s3://{bucket}/{latest['Key']}"

def _ensure_create_model(model_name, image_uri, model_data_url, exec_role):
    container = {
        "Image": image_uri,
        "ModelDataUrl": model_data_url,
        "Environment": {
            # 필요시 사용자 환경변수 추가
            "SAGEMAKER_PROGRAM": "serve.py",
            "SAGEMAKER_REGION": os.environ.get("AWS_REGION", "")
        },
    }
    try:
        sm.create_model(
            ModelName=model_name,
            ExecutionRoleArn=exec_role,
            PrimaryContainer=container,
        )
    except ClientError as e:
        msg = str(e)
        # 이미 존재하면 통과
        if e.response["Error"]["Code"] == "ValidationException" and "Already exists" in msg:
            return
        raise

def deploy(endpoint_name, image_uri, model_data_url, model_prefix, exec_role,
           alarm5, alarm_latency, instance_type, instance_count,
           canary_percent, canary_wait, term_wait):

    # ── 0) model.tar.gz auto resolve if prefix given
    if not model_data_url and model_prefix:
        model_data_url = _latest_model_tar(model_prefix)
    if not model_data_url:
        raise ValueError("One of --model-data-url or --model-prefix is required")

    # ── 1) names
    suffix = str(int(time.time()))
    model_name = f"{endpoint_name}-{suffix}"
    cfg_name   = f"{endpoint_name}-{model_name}"

    # ── 2) Model
    _ensure_create_model(model_name, image_uri, model_data_url, exec_role)

    # ── 3) EndpointConfig (DataCapture on)
    capture_s3 = os.environ.get("CAPTURE_S3_URI")
    if not capture_s3:
        raise ValueError("CAPTURE_S3_URI env is required")
    sm.create_endpoint_config(
        EndpointConfigName=cfg_name,
        ProductionVariants=[{
            "VariantName": "AllTraffic",
            "ModelName": model_name,
            "InitialInstanceCount": int(instance_count),
            "InstanceType": instance_type,
            "InitialVariantWeight": 1.0
        }],
        DataCaptureConfig={
            "EnableCapture": True,
            "InitialSamplingPercentage": 100,
            "DestinationS3Uri": capture_s3,
            "CaptureOptions": [{"CaptureMode": "Input"}, {"CaptureMode": "Output"}],
            "CaptureContentTypeHeader": {"JsonContentTypes": ["application/json", "application/jsonlines"]},
        },
    )

    # ── 4) Endpoint exists?
    exists = True
    try:
        sm.describe_endpoint(EndpointName=endpoint_name)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ValidationException", "ResourceNotFound"):
            exists = False
        else:
            raise

    # ── 5) Blue/Green config
    alarms = []
    a5 = alarm5 or f"{endpoint_name}-5xx"
    al = alarm_latency or f"{endpoint_name}-latency-p95"
    if a5: alarms.append({"AlarmName": a5})
    if al: alarms.append({"AlarmName": al})
    deploy_cfg = {
        "BlueGreenUpdatePolicy": {
            "TrafficRoutingConfiguration": {
                "Type": "CANARY",
                "WaitIntervalInSeconds": int(canary_wait),
                "CanarySize": {"Type": "CAPACITY_PERCENT", "Value": float(canary_percent)},
            },
            "TerminationWaitInSeconds": int(term_wait),
        }
    }
    if alarms:
        deploy_cfg["AutoRollbackConfiguration"] = {"Alarms": alarms}

    # ── 6) Create or Update
    if not exists:
        sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=cfg_name)
        _wait_endpoint(endpoint_name, "InService")
        # (선택) 동일 컨피그 재적용하여 Blue/Green 정책 세팅
        sm.update_endpoint(EndpointName=endpoint_name, EndpointConfigName=cfg_name, DeploymentConfig=deploy_cfg)
        _wait_endpoint(endpoint_name, "InService")
    else:
        sm.update_endpoint(EndpointName=endpoint_name, EndpointConfigName=cfg_name, DeploymentConfig=deploy_cfg)
        _wait_endpoint(endpoint_name, "InService")

    print(f"deployed model={model_name}, config={cfg_name}, endpoint={endpoint_name}, model_data={model_data_url}")

if __name__ == "__main__":
    import time
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", required=True)
    p.add_argument("--image", required=True, help="ECR image URI")
    p.add_argument("--model-data-url", required=False, help="S3 URI to model.tar.gz")
    p.add_argument("--model-prefix", required=False, help="S3 prefix to search latest tar.gz (e.g. s3://bucket/path/)")
    p.add_argument("--exec-role", required=True)
    p.add_argument("--alarm-5xx", dest="alarm_5xx", default="")
    p.add_argument("--alarm-latency", default="")
    p.add_argument("--instance-type", default="ml.m5.large")
    p.add_argument("--instance-count", default="1")
    p.add_argument("--canary-percent", default="10")
    p.add_argument("--canary-wait", default="600")
    p.add_argument("--termination-wait", default="300")
    args = p.parse_args()

    deploy(
        endpoint_name=args.endpoint,
        image_uri=args.image,
        model_data_url=args.model_data_url,
        model_prefix=args.model_prefix,
        exec_role=args.exec_role,
        alarm5=args.alarm_5xx,
        alarm_latency=args.alarm_latency,
        instance_type=args.instance_type,
        instance_count=args.instance_count,
        canary_percent=args.canary_percent,
        canary_wait=args.canary_wait,
        term_wait=args.termination_wait,
    )

