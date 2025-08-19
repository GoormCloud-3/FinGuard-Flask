import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
import os
import json, tarfile, sys

#0. set path
test_path = "/opt/ml/processing/test/test.csv"
model_dir = "/opt/ml/processing/model"
model_tar = os.path.join(model_dir, "model.tar.gz")
model_path = os.path.join(model_dir, "xgboost-model")
output_path = "/opt/ml/processing/evaluation/evaluation.json"

#1. unzip model artifact
if os.path.exists(model_tar):
    with tarfile.open(model_tar) as tar:
        tar.extractall(model_dir)

if not os.path.exists(model_path):
    raise FileNotFoundError(f"[EVAL] model file not found: {model_path} (or {model_tar})")

#2. load data
test_df = pd.read_csv(test_path)
if "fraud" not in test_df.columns:
    raise ValueError(f"[EVAL] 'fraud' column missing in test.csv columns={list(df.columns)}")
X_test = test_df.drop("fraud", axis=1)
y_test = test_df["fraud"]

#3. load model
dtest = xgb.DMatrix(X_test)
model = xgb.Booster()
model.load_model(model_path)

#4. predict and check AUC
y_proba = model.predict(dtest)
auc = roc_auc_score(y_test, y_proba)

#5. save result
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump({"metrics":{"auc": float(auc)}}, f)
