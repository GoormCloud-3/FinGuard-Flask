import os
import pandas as pd
import sys
import subprocess
from sklearn.model_selection import train_test_split

try:    
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler
    from imblearn.pipeline import Pipeline as ImbPipeline
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "imbalanced-learn"])
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler
    from imblearn.pipeline import Pipeline as ImbPipeline

# load data
df = pd.read_csv("/opt/ml/processing/input/finguard_transdata.csv")
X = df.drop("fraud", axis=1)
y = df["fraud"]

# devide Train/Test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# SMOTE(OverSamplig) + UnderSampling
over = SMOTE(sampling_strategy=0.1, random_state=42)
under = RandomUnderSampler(sampling_strategy=0.5, random_state=42)
imb_pipeline = ImbPipeline(steps=[("smote", over), ("under", under)])

X_resampled, y_resampled = imb_pipeline.fit_resample(X_train, y_train)

##save in csv
#recover names of columns of SMOTE result
train_X_df = pd.DataFrame(X_resampled, columns=X_train.columns)
train_y_sr = pd.Series(y_resampled, name="fraud")

# set label to first column (the rule of XGBoost)
train = pd.concat([train_y_sr, train_X_df], axis=1)

# maintain frame
test = pd.concat([X_test, y_test.rename("fraud")], axis=1)

train_output = "/opt/ml/processing/train"
test_output = "/opt/ml/processing/test"
os.makedirs(train_output, exist_ok=True)
os.makedirs(test_output, exist_ok=True)

train.to_csv(f'{train_output}/train.csv', index=False)
test.to_csv(f'{test_output}/test.csv', index=False)


