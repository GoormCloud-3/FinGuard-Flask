import argparse, boto3

sm = boto3.client("sagemaker")

def deploy(endpoint_name, model_package_arn, image_uri, exec_role,
           alarm5, alarm_latency, instance_type, instance_count,
           canary_percent, canary_wait, term_wait):

    suffix = model_package_arn.split("/")[-1]
    model_name = f"{endpoint_name}-{suffix}"

    # 1) Model
    sm.create_model(
        ModelName=model_name,
        ExecutionRoleArn=exec_role,
        PrimaryContainer={
            "Image": image_uri,
            "ModelPackageName": model_package_arn
        }
    )

    # 2) EndpointConfig
    cfg_name = f"{endpoint_name}-{model_name}"
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
            "DestinationS3Uri": os.environ.get("CAPTURE_S3_URI"),
            "CaptureOptions": [{"CaptureMode": "Input"}, {"CaptureMode": "Output"}],
            "CaptureContentTypeHeader": {
                "JsonContentTypes": ["application/json", "application/jsonlines"]
            }
        }
    )

    # 3) UpdateEndpoint with Blue/Green
    alarms = []
    # 비어 있으면 규칙에 따라 자동 이름 사용 (<endpoint>-5xx / <endpoint>-latency-p95)
    a5 = alarm5 or f"{endpoint_name}-5xx"
    al = alarm_latency or f"{endpoint_name}-latency-p95"
    # 알람이 실제 존재하지 않아도 API는 통과하므로, 사전에 이름을 정확히 맞추어 생성해야 함
    if a5: alarms.append({"AlarmName": a5})
    if al: alarms.append({"AlarmName": al})

    dc = {
        "BlueGreenUpdatePolicy": {
            "TrafficRoutingConfiguration": {
                "Type": "CANARY",
                "WaitIntervalInSeconds": int(canary_wait),
                "CanarySize": {"Type": "CAPACITY_PERCENT", "Value": float(canary_percent)}
            },
            "TerminationWaitInSeconds": int(term_wait)
        }
    }
    if alarms:
        dc["AutoRollbackConfiguration"] = {"Alarms": alarms}

    sm.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=cfg_name,
        DeploymentConfig=dc
    )
    print(f"deployed model={model_name}, config={cfg_name}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", required=True)
    p.add_argument("--package", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--exec-role", required=True)
    p.add_argument("--alarm-5xx", default="")
    p.add_argument("--alarm-latency", default="")
    p.add_argument("--instance-type", default="ml.m5.large")
    p.add_argument("--instance-count", default="1")
    p.add_argument("--canary-percent", default="10")
    p.add_argument("--canary-wait", default="600")
    p.add_argument("--termination-wait", default="300")
    args = p.parse_args()

    deploy(
        args.endpoint, args.package, args.image, args.exec_role,
        args.alarm_5xx, args.alarm_latency, args.instance_type, args.instance_count,
        args.canary_percent, args.canary_wait, args.termination_wait
    )

