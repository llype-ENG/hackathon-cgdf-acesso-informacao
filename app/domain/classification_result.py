from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    reason: str
    confidence: float = 0.0
    details: Optional[list[str]] = field(default=None)

    def to_dict(self) -> dict:
        payload = {
            "classification": self.classification,
            "reason": self.reason,
            "confidence": self.confidence,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload
