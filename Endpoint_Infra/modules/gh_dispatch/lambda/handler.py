import json, os, boto3, urllib.request, urllib.error, logging

log = logging.getLogger()
log.setLevel(logging.INFO)

secrets = boto3.client("secretsmanager")
OWNER = os.environ["GITHUB_OWNER"]
REPO  = os.environ["GITHUB_REPO"]
SECRET_ARN = os.environ["GITHUB_SECRET_ARN"]
EVENT_TYPE = os.environ.get("EVENT_TYPE", "model-approved")

def _token():
    sec = secrets.get_secret_value(SecretId=SECRET_ARN)
    s = sec.get("SecretString") or ""
    tok = json.loads(s).get("token") if s.startswith("{") else s
    return tok.strip()

def lambda_handler(event, _ctx):
    log.info("RAW EVENT: %s", json.dumps(event)[:1500])

    detail = event.get("detail") or {}
    pkg_arn = detail.get("ModelPackageArn")
    log.info("DETAIL KEYS: %s", list(detail.keys()))

    if not pkg_arn:
        log.warning("ModelPackageArn not found in event.detail")

    body = {
        "event_type": EVENT_TYPE,
        "client_payload": {"model_package_arn": pkg_arn},
    }
    data = json.dumps(body).encode("utf-8")
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {_token()}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "aws-lambda-repo-dispatch",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info("GITHUB RESP: status=%s, headers=%s", resp.status, dict(resp.headers.items()))
            # repository_dispatch 성공 시 보통 204 No Content
            return {"status": resp.status, "dispatched_type": EVENT_TYPE, "package": pkg_arn}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        log.error("HTTPError %s %s headers=%s body=%s", e.code, e.reason, dict(e.headers.items()), body)
        return {"status": e.code, "error": e.reason, "body": body}
    except Exception as e:
        log.exception("UNEXPECTED ERROR")
        return {"status": 599, "error": str(e)}
