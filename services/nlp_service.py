import joblib

class NLPService:
    def __init__(self, model_path="model.pkl", vectorizer_path="vectorizer.pkl"):
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

    def predict(self, text: str) -> dict:
        if not text:
            return {"risk": False, "confidence": 0.0}

        X = self.vectorizer.transform([text])
        prob = self.model.predict_proba(X)[0][1]

        return {
            "risk": prob > 0.6,
            "confidence": float(prob)
        }



