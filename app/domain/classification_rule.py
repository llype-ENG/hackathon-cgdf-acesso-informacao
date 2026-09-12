from abc import ABC, abstractmethod

from app.domain.classification_result import ClassificationResult


class ClassificationRule(ABC):
    @abstractmethod
    def evaluate(self, text: str) -> ClassificationResult | None:
        """Return a classification result when the rule applies; otherwise None."""
