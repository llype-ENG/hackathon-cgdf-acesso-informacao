from services.regex_service import detect_regex
from services.nlp_service import NLPService

nlp = NLPService()

def classify(text: str) -> dict:
    regex_result = detect_regex(text)

    if regex_result["has_personal_data"]:
        return {
            "classification": "NÃO PÚBLICO",
            "reason": "Dados pessoais explícitos",
            "details": regex_result["matches"]
        }

    nlp_result = nlp.predict(text)

    if nlp_result["risk"]:
        return {
            "classification": "NÃO PÚBLICO",
            "reason": "Identificação indireta",
            "confidence": nlp_result["confidence"]
        }

    return {
        "classification": "PÚBLICO",
        "reason": "Nenhum risco identificado"
    }
