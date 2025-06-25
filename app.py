from flask import Flask, request, jsonify
from wrapper import XGBThresholdWrapper
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load("Model/xgb_threshold_08.pkl")

# 헬스 체크용 (for SageMaker Endpoint)
@app.route('/ping', methods=['GET'])
def ping():
    return "OK", 200

# 추론 요청
@app.route('/invocations', methods=['POST'])
def invoke():
    try:
        data = request.get_json()

        if "features" not in data:
            return jsonify({"error": "'features' field is required"}), 400

        features = np.array(data["features"]).reshape(1, -1)

        # 확률 예측
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
    app.run(host="0.0.0.0", port=5000)