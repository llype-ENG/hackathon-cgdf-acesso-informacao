from pathlib import Path

import joblib


class ModelLoader:
    def __init__(self, model_path: str | None = None, vectorizer_path: str | None = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.model_path = Path(model_path) if model_path else base_dir / "model.pkl"
        self.vectorizer_path = Path(vectorizer_path) if vectorizer_path else base_dir / "vectorizer.pkl"

    def load(self):
        model = joblib.load(str(self.model_path))
        vectorizer = joblib.load(str(self.vectorizer_path))
        model.vectorizer = vectorizer
        return model
