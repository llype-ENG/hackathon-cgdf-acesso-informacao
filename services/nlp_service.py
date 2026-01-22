import joblib

CONTEXT_MAP = {
    0: "NEUTRO",
    1: "PESSOAL",
    2: "AMBIGUO"
}

class NLPService:
    def __init__(self,
                 model_path="context_model.pkl",
                 vectorizer_path="context_vectorizer.pkl"):
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

    def predict_context(self, text: str) -> dict:
        if not text:
            return {"context": "NEUTRO", "confidence": 0.0}

        X = self.vectorizer.transform([text])
        probs = self.model.predict_proba(X)[0]

        label = probs.argmax()
        confidence = probs[label]

        return {
            "context": CONTEXT_MAP[label],
            "confidence": float(confidence)
        }
