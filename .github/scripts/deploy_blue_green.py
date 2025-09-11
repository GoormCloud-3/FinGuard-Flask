# .github/scripts/deploy_blue_green.py
import argparse
import os
import time
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

sm = boto3.client("sagemaker")
s3 = boto3.client("s3")


# ---------- Utilities ----------
def _now_suffix() -> str:
    return str(int(time.time()))


def _wait_endpoint(endpoint_name: str, status: str = "InService", timeout: int = 7200, poll: int = 20):
    """Poll until endpoint reaches desired status."""
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


def _latest_model_tar(s3_prefix: str, require_suffix: str = "/output/model.tar.gz") -> str:
    """
    s3_prefix: e.g. s3://finguard-model-artifacts/model/
    returns:   e.g. s3://.../pipelines-.../output/model.tar.gz (latest by LastModified)
    """
    u = urlparse(s3_prefix)
    if u.scheme != "s3" or not u.netloc:
        raise ValueError(f"Invalid S3 prefix: {s3_prefix}")
    bucket = u.netloc
    prefix = u.path.lstrip("/")

    paginator = s3.get_paginator("list_objects_v2")
    latest = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(require_suffix):
                continue
            if (latest is None) or (obj["LastModified"] > latest["LastModified"]):
                latest = obj

    if not latest:
        # Debug hints (last 20 keys)
        hints = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            hints.extend(page.get("Contents", []))
        hints = sorted(hints, key=lambda x: x["LastModified"], reverse=True)[:20]
        print("No matches. Recent keys under prefix:")
        for h in hints:
            print(h["Key"])
        raise FileNotFoundError(f"No *{require_suffix} under {s3_prefix}")

    return f"s3://{bucket}/{latest['Key']}"


def _ensure_create_model(model_name: str, image_uri: str, model_data_url: str, exec_role: str):
    """Create Model if not exists (idempotent)."""
    container = {
        "Image": image_uri,
        "ModelDataUrl": model_data_url,
        "Environment": {
            "SAGEMAKER_PROGRAM": "serve.py",  # 엔트리포인트
            "SAGEMAKER_REGION": os.environ.get("AWS_REGION", ""),
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
        if e.response["Error"]["Code"] == "ValidationException" and "Already exists" in msg:
            return
        raise


def _unique_names(endpoint_name: str):
    suffix = _now_suffix()
    model_name = f"fraud-model-{suffix}"
    cfg_name = f"fraud-cfg-{suffix}"
    return model_name, cfg_name


# ---------- Main deploy ----------
def deploy(
    endpoint_name: str,
    image_uri: str,
    model_data_url: str,
    model_prefix: str,
    exec_role: str,
    alarm5: str,
    alarm_latency: str,
    instance_type: str,
    instance_count: int,
    canary_percent: int,
    canary_wait: int,
    term_wait: int,
):
    # 0) resolve model tar
    if not model_data_url and model_prefix:
        model_data_url = _latest_model_tar(model_prefix, require_suffix="/output/model.tar.gz")
    if not model_data_url:
        raise ValueError("One of --model-data-url or --model-prefix is required")

    # 1) names
    model_name, cfg_name = _unique_names(endpoint_name)

    # 2) Model
    _ensure_create_model(model_name, image_uri, model_data_url, exec_role)

    # 3) EndpointConfig (with DataCapture)
    capture_s3 = os.environ.get("CAPTURE_S3_URI")
    if not capture_s3:
        raise ValueError("CAPTURE_S3_URI env is required")
    sm.create_endpoint_config(
        EndpointConfigName=cfg_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InitialInstanceCount": int(instance_count),
                "InstanceType": instance_type,
                "InitialVariantWeight": 1.0,
            }
        ],
        DataCaptureConfig={
            "EnableCapture": True,
            "InitialSamplingPercentage": 100,
            "DestinationS3Uri": capture_s3,
            "CaptureOptions": [{"CaptureMode": "Input"}, {"CaptureMode": "Output"}],
            "CaptureContentTypeHeader": {"JsonContentTypes": ["application/json", "application/jsonlines"]},
        },
    )

    # 4) endpoint existence
    exists = True
    try:
        sm.describe_endpoint(EndpointName=endpoint_name)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ValidationException", "ResourceNotFound"):
            exists = False
        else:
            raise

    if not exists:
        # 5) first-time create (no BG/alarms)
        sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=cfg_name)
        _wait_endpoint(endpoint_name, "InService")
        print(f"[create] endpoint={endpoint_name}, cfg={cfg_name}, model={model_name}, data={model_data_url}")
        return

    # 6) update with Blue/Green + AutoRollback(alarms)
    cp = int(canary_percent)
    cp = max(1, min(100, cp))

    deploy_cfg = {
        "BlueGreenUpdatePolicy": {
            "TrafficRoutingConfiguration": {
                "Type": "CANARY",
                "WaitIntervalInSeconds": int(canary_wait),
                "CanarySize": {"Type": "CAPACITY_PERCENT", "Value": cp},
            },
            "TerminationWaitInSeconds": int(term_wait),
        }
    }

    alarms = []
    a5 = (alarm5 or f"{endpoint_name}-5xx").strip()
    al = (alarm_latency or f"{endpoint_name}-latency-p95").strip()
    if a5:
        alarms.append({"AlarmName": a5})
    if al:
        alarms.append({"AlarmName": al})
    if alarms:
        deploy_cfg["AutoRollbackConfiguration"] = {"Alarms": alarms}

    sm.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=cfg_name,  # must be a new config name
        DeploymentConfig=deploy_cfg,
    )
    _wait_endpoint(endpoint_name, "InService")
    print(f"[update] endpoint={endpoint_name}, cfg={cfg_name}, model={model_name}, data={model_data_url}, canary={cp}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--image", required=True, help="ECR image URI")
    ap.add_argument("--model-data-url", required=False, help="S3 URI to model.tar.gz")
    ap.add_argument("--model-prefix", required=False, help="S3 prefix to search latest tar.gz (e.g. s3://bucket/path/)")
    ap.add_argument("--exec-role", required=True)
    ap.add_argument("--alarm-5xx", dest="alarm_5xx", default="")
    ap.add_argument("--alarm-latency", default="")
    ap.add_argument("--instance-type", default="ml.m5.large")
    ap.add_argument("--instance-count", type=int, default=1)
    ap.add_argument("--canary-percent", type=int, default=10)
    ap.add_argument("--canary-wait", type=int, default=600)
    ap.add_argument("--termination-wait", type=int, default=300)
    args = ap.parse_args()

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

