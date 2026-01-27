from services.regex_service import RegexService
from services.ner_service import extract_entities_dual
from services.nlp_service import NLPService

regex_service = RegexService()
nlp_service = NLPService()

# =========================
# CONFIGURAÇÕES
# =========================
EXPLICIT_TYPES = {"CPF", "RG", "EMAIL", "PHONE", "ADDRESS", "MATRICULA"}

ABSTRACT_TERMS = {
    "administração", "gestão", "integridade", "capacidades",
    "política", "programa", "unidade", "plano",
    "estado", "órgão", "entidade", "secretaria",
    "departamento", "coordenação", "controle"
}

PERSONAL_TRIGGERS = [
    "meu nome é",
    "sou ",
    "fui ",
    "trabalhei",
    "necessito",
    "solicitei",
    "recebi",
    "bolsa",
    "vaga de emprego"
]

# =========================
# HELPERS
# =========================
def has_personal_context(text: str) -> bool:
    text_lower = text.lower()
    return any(t in text_lower for t in PERSONAL_TRIGGERS)


def is_human_candidate(name: str) -> bool:
    words = name.lower().split()

    # Muito curto para pessoa
    if len(words) < 2:
        return False

    # Termos abstratos / institucionais
    if any(w in ABSTRACT_TERMS for w in words):
        return False

    return True


def build_result(classification, reason, confidence):
    return {
        "classification": classification,
        "reason": reason,
        "confidence": round(float(confidence), 2)
    }

# =========================
# CLASSIFICADOR
# =========================
def classify(text: str) -> dict:
    if not text or not text.strip():
        return build_result("PÚBLICO", "Texto vazio", 1.0)

    # =========================
    # REGEX
    # =========================
    regex_result = regex_service.detect(text)

    explicit = regex_result["explicit"]     # CPF, RG, EMAIL, etc
    names = regex_result["names"]           # nomes detectados por regex
    has_signature = regex_result["signature"]

    # =========================
    # NER (SpaCy)
    # =========================
    spacy_persons, spacy_orgs = extract_entities_dual(text)

    regex_names = [n["value"] for n in names]

    human_names = [
        n for n in regex_names
        if is_human_candidate(n) and n in spacy_persons
    ]

    # =========================
    # 1️⃣ DADOS EXPLÍCITOS (DECISÃO AUTOMÁTICA)
    # =========================
    for m in explicit:
        if m["type"] in EXPLICIT_TYPES:
            return build_result(
                "NÃO PÚBLICO",
                f"Dado pessoal explícito: {m['type']}",
                0.99
            )

    # =========================
    # 2️⃣ CONTEXTO PESSOAL DIRETO
    # =========================
    if human_names and has_personal_context(text):
        return build_result(
            "NÃO PÚBLICO",
            f"Dado pessoal em contexto pessoal direto: {human_names}",
            0.99
        )

    # =========================
    # 3️⃣ ASSINATURA (SINAL FORTE)
    # =========================
    if has_signature and human_names:
        return build_result(
            "NÃO PÚBLICO",
            f"Nome humano em assinatura: {human_names}",
            0.95
        )

    # =========================
    # 4️⃣ NLP (DESEMPATE)
    # =========================
    if human_names:
        nlp = nlp_service.predict_context(text)

        if nlp["context"] == "PESSOAL":
            return build_result(
                "NÃO PÚBLICO",
                f"Nome humano em contexto pessoal: {human_names}",
                nlp["confidence"]
            )

        return build_result(
            "REAVALIAÇÃO HUMANA",
            f"Nome humano sem contexto pessoal explícito: {human_names}",
            max(nlp["confidence"], 0.6)
        )

    # =========================
    # 5️⃣ APENAS ENTIDADES INSTITUCIONAIS
    # =========================
    if spacy_orgs and not spacy_persons:
        return build_result(
            "PÚBLICO",
            "Texto com entidades institucionais apenas",
            0.95
        )

    # =========================
    # 6️⃣ TEXTO LIMPO
    # =========================
    return build_result(
        "PÚBLICO",
        "Nenhum dado pessoal identificado",
        1.0
    )
