from app.domain.classification_result import ClassificationResult
from app.domain.classification_rule import ClassificationRule
from app.infrastructure.model_loader import ModelLoader


class NlpRiskRule(ClassificationRule):
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader

    def evaluate(self, text: str) -> ClassificationResult | None:
        if not text or not str(text).strip():
            return None

        model = self.model_loader.load()
        probability = model.predict_proba(model.vectorizer.transform([str(text)]))[0][1]
        risk = probability > 0.6

        if not risk:
            return None

        return ClassificationResult(
            classification="NÃO PÚBLICO",
            reason="Identificação indireta",
            confidence=float(probability),
        )
