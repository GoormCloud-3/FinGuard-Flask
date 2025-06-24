from flask import Flask, request, jsonify
import joblib
import numpy as np
app = Flask(__name__)
model = joblib.load("Model/xgb_threshold_08.pkl")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    features = np.array(data["features"]).reshape(1,-1)
    pred = int(model.predict(features)[0])
    return jsonify({"prediction": pred})

