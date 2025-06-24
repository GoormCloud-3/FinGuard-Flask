from flask import Flask, request, jsonify
from wrapper import XGBThresholdWrapper
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load("Model/xgb_threshold_08.pkl")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    features = np.array(data["features"]).reshape(1, -1)

    # 예측 확률
    prob = float(model.predict_proba(features)[0][1])
    pred = int(prob > model.threshold) if hasattr(model, "threshold") else int(model.predict(features)[0])

    return jsonify({
        "prediction": pred,
        "probability": round(prob, 4),
        "threshold": getattr(model, "threshold", "N/A"),
        "input": data["features"]
    })

