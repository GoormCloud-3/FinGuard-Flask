# serve.py
from flask import Flask, request, jsonify
import os, io, json, logging
import numpy as np
import pandas as pd
import xgboost as xgb

# setting
MODEL_FILE = os.getenv("MODEL_FILE", "/opt/ml/model/xgboost-model")
THRESHOLD = float(os.getenv("THRESHOLD", "0.5"))

app = Flask(__name__)
logger = logging.getLogger("inference")
logging.basicConfig(level=logging.INFO)

_booster = None

# 1) load model
def load_model():
    global _booster
    if _booster is None:
        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")
        booster = xgb.Booster()
        booster.load_model(MODEL_FILE)
        _booster = booster
        logger.info("Model loaded from %s", MODEL_FILE)
    return _booster

# 2) parsing inputs(JSON or CSV or ROW) 
def _dmatrix_from_request():
    ctype = (request.headers.get("Content-Type") or "").lower()

    if "application/json" in ctype:
        payload = request.get_json(force=True, silent=False)
        if isinstance(payload, dict):
            if "instances" in payload:
                arr = np.array(payload["instances"], dtype="float32")
                raw = {"instances": payload["instances"]}
            elif "features" in payload:
                arr = np.array([payload["features"]], dtype="float32")
                raw = {"features": payload["features"]}
            else:
                raise ValueError("JSON must contain 'instances' or 'features'.")
        elif isinstance(payload, list):
            arr = np.array(payload, dtype="float32")
            raw = {"instances": payload}
        else:
            raise ValueError("Unsupported JSON format.")
        return xgb.DMatrix(arr), raw, "application/json"

    elif "text/csv" in ctype:
        data = request.data.decode("utf-8")
        df = pd.read_csv(io.StringIO(data), header=None)
        return xgb.DMatrix(df.values.astype("float32")), {"csv": data}, "text/csv"

    else:
        raise ValueError(f"Unsupported Content-Type: {ctype}")

# 3) health check
@app.route("/ping", methods=["GET"])
def ping():
    try:
        load_model()
        return "OK", 200
    except Exception as e:
        logger.exception("Ping failed: %s", e)
        return f"Model not loaded: {e}", 500

# 4) start inference
@app.route("/invocations", methods=["POST"])
def invocations():
    try:
        #predict
        booster = load_model()
        dmat, raw, _ = _dmatrix_from_request()
        probs = booster.predict(dmat).tolist()  # binary:logistic -> probability
        preds = [1 if p >= THRESHOLD else 0 for p in probs]
        #serialize output
        return jsonify({
            "predictions": preds,
            "probabilities": probs,
            "threshold": THRESHOLD,
            "input": raw
        }), 200
    except Exception as e:
        logger.exception("Invocation failed: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # SageMake Rule: fix port num, 8080
    app.run(host="0.0.0.0", port=8080)
