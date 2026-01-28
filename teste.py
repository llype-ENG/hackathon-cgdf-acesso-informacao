from services.regex_service import RegexService
from services.classifier import ClassificationService
import json

text = """Por gentileza,   Gostaria de obter dados de violência psicológica contra a mulher de 2015 a 2025. Estou fazendo uma pesquisa de mestrado e gostaria de fazer essa comparação antes da pandemia.    Grata Conceição Sampaio"""
# =========================
# TESTE REGEX
# =========================
service = RegexService()
regex_result = service.detect(text)

print("=== REGEX RESULT ===")
print(json.dumps(regex_result, indent=2, ensure_ascii=False))

# =========================
# TESTE CLASSIFIER
# =========================
svc = ClassificationService()
classification_result = svc.classify(text)

print("\n=== CLASSIFIER RESULT ===")
print(json.dumps(classification_result, indent=2, ensure_ascii=False))
