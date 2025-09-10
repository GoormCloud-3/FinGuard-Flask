import json, os, boto3, urllib.request

secrets = boto3.client("secretsmanager")
OWNER = os.environ["GITHUB_OWNER"]
REPO  = os.environ["GITHUB_REPO"]
SECRET_ARN = os.environ["GITHUB_SECRET_ARN"]
EVENT_TYPE = os.environ.get("EVENT_TYPE", "model-approved")

def _token():
    sec = secrets.get_secret_value(SecretId=SECRET_ARN)
    s = sec.get("SecretString") or ""
    return json.loads(s).get("token") if s.startswith("{") else s

def lambda_handler(event, _ctx):
    pkg_arn = event["detail"]["ModelPackageArn"]
    body = { "event_type": EVENT_TYPE,
             "client_payload": {"model_package_arn": pkg_arn} }
    data = json.dumps(body).encode()

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_token()}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        return {"status": resp.status, "package": pkg_arn}

