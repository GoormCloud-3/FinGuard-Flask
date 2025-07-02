#!/usr/bin/env python3
from flask import Flask, request, jsonify
import joblib
import numpy as np
import os

# for threshold branch logic
try:
    from wrapper import XGBThresholdWrapper
    use_wrapper = True
except ImportError:
    use_wrapper = False

app = Flask(__name__)
MODEL_PATH = "/opt/ml/model/xgb_threshold_08.pkl"

#load model
model = None
def load_model():
    global model
    if model is not None:
        return model
    if use_wrapper:
        model = XGBThresholdWrapper(joblib.load(MODEL_PATH))
    else:
        model = joblib.load(MODEL_PATH)
    return model

#for health check
@app.route('/ping', methods=['GET'])
def ping():
    try:
        _ = load_model()  # check the existence of model
        return "OK", 200
    except:
        return f"Model not loaded: {e}", 500

#for prediction
@app.route('/invocations', methods=['POST'])
def invoke():
    try:
        model = load_model()
        data = request.get_json()
        if "features" not in data:
            return jsonify({"error": "'features' field is required"}), 400

        features = np.array(data["features"]).reshape(1, -1)
        prob = float(model.predict_proba(features)[0][1])
        pred = int(prob > model.threshold) if hasattr(model, "threshold") else int(model.predict(features)[0])
        return jsonify({
            "prediction": pred,
            "probability": round(prob, 4),
            "threshold": getattr(model, "threshold", "N/A"),
            "input": data["features"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
