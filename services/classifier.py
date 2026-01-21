from services.regex_service import detect_regex
from services.nlp_service import NLPService

nlp = NLPService()

def classify(text: str) -> dict:
    # Camada 1 — Regex (REGRA DO EDITAL)
    regex_result = detect_regex(text)

    if regex_result["has_personal_data"]:
        return {
            "classification": "NÃO PÚBLICO",
            "reason": f"Dado pessoal explícito: {regex_result['matches']}",
            "confidence": 1.0
        }

    # Camada 2 — NLP (APOIO, NÃO DECISÃO)
    nlp_result = nlp.predict(text)
    confidence = nlp_result["confidence"]

    if nlp_result["risk"]:
        return {
            "classification": "REAVALIAÇÃO HUMANA",
            "reason": "Possível identificação indireta (NLP)",
            "confidence": confidence
        }

    return {
        "classification": "PÚBLICO",
        "reason": "Nenhum dado pessoal explícito",
        "confidence": confidence
    }
