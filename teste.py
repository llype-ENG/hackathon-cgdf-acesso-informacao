from services.regex_service import RegexService
from services.classifier import classify
import json

text = """Prezados!  Gostaria de solicitar a declaração de exercício findo da servidora AURA Costa Mota (matrícula 98.123-3), na qualidade de sua representante.  Preciso do montante que ela tem a receber referente a despesas de exercícios encerrados.  Para tanto, encaminho procuração, substabelecimento, cópia do documento do constituinte e minha OAB.  Att.,  Rafael"""
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
classification_result = classify(text)

print("\n=== CLASSIFIER RESULT ===")
print(json.dumps(classification_result, indent=2, ensure_ascii=False))
