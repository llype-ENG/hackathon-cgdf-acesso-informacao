import regex as re

from app.domain.classification_result import ClassificationResult
from app.domain.classification_rule import ClassificationRule

CPF_REGEX = re.compile(r'\b\d{3}\.??\d{3}\.??\d{3}-?\d{2}\b')
EMAIL_REGEX = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b', re.IGNORECASE)
PROCESS_REGEX = re.compile(r'\b\d{4,6}-\d{6,8}/\d{4}-\d{2}\b')
PHONE_REGEX = re.compile(
    r'\b(?:\+55\s*)?(?:\(?\d{2}\)?\s*)?(?:9?\d{4})[-\s]?\d{4}\b'
)
RG_REGEX = re.compile(
    r'\b(?:RG|Registro\s+Geral)\s*[:\-]?\s*\d{1,2}\.??\d{3}\.??\d{3}-?[A-Za-z0-9]\b',
    re.IGNORECASE,
)
NAME_REGEX = re.compile(
    r'\b('
    r'meu nome é|me chamo|assinado por|atenciosamente|att'
    r')\b'
    r'[\s\.,:;-]*'
    r'[A-ZÁ-Ú][a-zá-ú]+'
    r'(?:\s+[A-ZÁ-Ú][a-zá-ú]+){0,3}',
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


class RegexPersonalDataRule(ClassificationRule):
    def evaluate(self, text: str) -> ClassificationResult | None:
        if not isinstance(text, str) or not text.strip():
            return None

        normalized_text = text.replace("\xa0", " ").strip()
        matches = []

        if EMAIL_REGEX.search(normalized_text):
            matches.append("EMAIL")
        if CPF_REGEX.search(normalized_text):
            matches.append("CPF")
        if RG_REGEX.search(normalized_text):
            matches.append("RG")
        if PHONE_REGEX.search(normalized_text) and not PROCESS_REGEX.search(normalized_text):
            matches.append("PHONE")
        if NAME_REGEX.search(normalized_text):
            matches.append("NAME")

        if not matches:
            return None

        return ClassificationResult(
            classification="NÃO PÚBLICO",
            reason="Dados pessoais explícitos",
            confidence=1.0,
            details=matches,
        )
