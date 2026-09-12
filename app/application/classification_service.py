from app.domain.classification_result import ClassificationResult
from app.domain.classification_rule import ClassificationRule
from app.domain.nlp_risk_rule import NlpRiskRule
from app.domain.regex_personal_data_rule import RegexPersonalDataRule
from app.infrastructure.model_loader import ModelLoader


class ClassificationService:
    def __init__(self, rules: list[ClassificationRule] | None = None):
        model_loader = ModelLoader()
        default_rules = [
            RegexPersonalDataRule(),
            NlpRiskRule(model_loader),
        ]
        self.rules = rules if rules is not None else default_rules

    def classify(self, text: str) -> dict:
        for rule in self.rules:
            result = rule.evaluate(text)
            if result is not None:
                return result.to_dict()

        return ClassificationResult(
            classification="PÚBLICO",
            reason="Nenhum risco identificado",
            confidence=0.0,
        ).to_dict()
