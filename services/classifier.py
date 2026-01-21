from services.regex_service import detect_regex
from services.nlp_service import NLPService

nlp = NLPService()

def classify(text: str) -> dict:
    # Camada 1 — Regex
    regex_result = detect_regex(text)

    if regex_result["has_personal_data"]:
        return {
            "classification": "NÃO PÚBLICO",
            "reason": f"Dado pessoal explícito: {regex_result['matches']}",
            "confidence": 1.0
        }

    # Camada 2 — NLP
    nlp_result = nlp.predict(text)
    confidence = nlp_result["confidence"]

    if nlp_result["risk"]:
        if confidence >= 0.75:
            return {
                "classification": "NÃO PÚBLICO",
                "reason": "Alto risco contextual (NLP)",
                "confidence": confidence
            }
        else:
            return {
                "classification": "REAVALIAÇÃO HUMANA",
                "reason": "Risco moderado (NLP)",
                "confidence": confidence
            }

    return {
        "classification": "PÚBLICO",
        "reason": "Nenhum risco identificado",
        "confidence": confidence
    }
