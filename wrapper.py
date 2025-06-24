#for 역직렬화
class XGBThresholdWrapper:
    def __init__(self, model, threshold=0.8):
        self.model = model
        self.threshold = threshold
    def predict(self, X):
        probs = self.model.predict_proba(X)[:, 1]
        return (probs > self.threshold).astype(int)
    def predict_proba(self, X):
        return self.model.predict_proba(X)