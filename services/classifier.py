from services.regex_service import detect_regex
from services.nlp_service import NLPService

nlp = NLPService()



def classify(text: str) -> dict:
    regex_result = detect_regex(text)

    # 1️⃣ Dado pessoal explícito → NÃO PÚBLICO
    if regex_result["has_personal_data"]:
        return {
            "classification": "NÃO PÚBLICO",
            "reason": f"Dado pessoal explícito: {regex_result['matches']}",
            "details": regex_result.get("ignored", []),
            "confidence": 1.0
        }

    # 2️⃣ Houve descarte contextual (empresa / institucional)
    if regex_result.get("ignored"):
        return {
            "classification": "PÚBLICO",
            "reason": "Referências institucionais ou empresariais não caracterizam dado pessoal",
            "details": regex_result["ignored"],
            "confidence": 1.0
        }

    # 3️⃣ NLP — só para ambiguidade
    ctx = nlp.predict_context(text)

    if ctx["context"] == "AMBIGUO":
        return {
            "classification": "REAVALIAÇÃO HUMANA",
            "reason": "Contexto ambíguo identificado por NLP",
            "confidence": ctx["confidence"]
        }

    # 4️⃣ Público padrão
    return {
        "classification": "PÚBLICO",
        "reason": "Nenhum dado pessoal identificado",
        "confidence": ctx["confidence"]
    }

