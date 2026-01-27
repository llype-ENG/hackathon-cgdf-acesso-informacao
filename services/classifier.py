# -*- coding: utf-8 -*-
from services.regex_service import RegexService
import re

# =========================
# NER (SpaCy) - opcional com fallback
# =========================
try:
    import spacy
    _NLP_PT = spacy.load("pt_core_news_sm")
except Exception:
    _NLP_PT = None  # fallback: sem NER

def _extract_spacy_entities(text: str):
    """
    Retorna (persons, orgs) usando SpaCy se disponível; caso contrário, ([], []).
    """
    if not _NLP_PT or not text:
        return [], []
    doc = _NLP_PT(text)
    persons = list({ent.text.strip() for ent in doc.ents if ent.label_ in ("PER", "PERSON")})
    orgs    = list({ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"})
    return persons, orgs

# =========================
# INSTÂNCIAS DE SERVIÇO
# =========================
regex_service = RegexService()

# =========================
# CONFIGURAÇÕES
# =========================
EXPLICIT_TYPES = {"CPF", "RG", "EMAIL", "PHONE", "ADDRESS", "MATRICULA"}

# Heurística de contexto pessoal (inclui “me chamo”)
PERSONAL_TRIGGERS = [
    "me chamo", "meu nome é",
    "sou ", "fui ", "trabalhei", "necessito",
    "solicitei", "recebi", "bolsa", "vaga de emprego",
    "meu imóvel", "minha casa", "minha residência", "meu endereço",
    "onde moro", "onde resido"
]

# =========================
# HELPERS
# =========================
def _normalize(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()

def has_personal_context(text: str) -> bool:
    tl = text.lower() if text else ""
    return any(t in tl for t in PERSONAL_TRIGGERS)

_ME_CHAMO_REGEX = re.compile(
    r'(?i)\bme\s+chamo\s+('
    r'[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+'
    r'(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){0,4}'
    r')'
)

def extract_name_after_me_chamo(text: str):
    """
    Retorna o nome logo após “me chamo …” (se houver); caso contrário None.
    """
    if not text:
        return None
    m = _ME_CHAMO_REGEX.search(text)
    return _normalize(m.group(1)) if m else None

def build_result(classification, reason, confidence):
    return {
        "classification": classification,
        "reason": reason,
        "confidence": round(float(confidence), 2)
    }

def classify(text: str) -> dict:
    if not text or not text.strip():
        return build_result("PÚBLICO", "Texto vazio", 1.0)

    # =========================
    # REGEX
    # =========================
    rx = regex_service.detect(text)
    explicit = rx["explicit"]     # EMAIL, CPF, etc (e ADDRESS se houver)
    signature = rx["signature"]
    signature_name = rx["signature_name"]
    regex_names = [n["value"] for n in rx["names"]]

    # =========================
    # 1) ASSINATURA (SEMPRE NÃO PÚBLICO)
    # =========================
    if signature and signature_name:
        return build_result(
            "NÃO PÚBLICO",
            f"Nome humano em assinatura: {signature_name}",
            0.95
        )

    # =========================
    # 2) DADOS EXPLÍCITOS
    # =========================
    for m in explicit:
        t = m.get("type")
        if t == "ADDRESS":
            # Endereço só é pessoal se houver contexto pessoal
            if has_personal_context(text):
                return build_result(
                    "NÃO PÚBLICO",
                    "Endereço pessoal identificado",
                    0.99
                )
            else:
                # endereço institucional / contexto neutro → ignora como dado pessoal
                continue
        # demais dados explícitos sempre pessoais
        if t in EXPLICIT_TYPES and t != "ADDRESS":
            return build_result(
                "NÃO PÚBLICO",
                f"Dado pessoal explícito: {t}",
                0.99
            )

    # =========================
    # 3) “ME CHAMO …”
    # =========================
    me_chamo_name = extract_name_after_me_chamo(text)
    if me_chamo_name:
        # “me chamo …” é forte indicativo de dado pessoal
        return build_result(
            "NÃO PÚBLICO",
            f"Nome humano em contexto pessoal direto (me chamo): {me_chamo_name}",
            0.99
        )

    # =========================
    # 4) NER (SpaCy): pessoas reais
    # =========================
    spacy_persons, spacy_orgs = _extract_spacy_entities(text)

    if spacy_persons:
        if has_personal_context(text):
            return build_result(
                "NÃO PÚBLICO",
                f"Nome humano em contexto pessoal: {spacy_persons}",
                0.98
            )
        # Sem contexto explícito → marcar para reavaliação
        return build_result(
            "REAVALIAÇÃO HUMANA",
            f"Nome humano sem contexto pessoal explícito: {spacy_persons}",
            0.75
        )

    # =========================
    # 5) APENAS ENTIDADES INSTITUCIONAIS
    # =========================
    if spacy_orgs and not spacy_persons:
        return build_result(
            "PÚBLICO",
            "Texto com entidades institucionais apenas",
            0.95
        )

    # =========================
    # 6) TEXTO LIMPO
    # =========================
    return build_result(
        "PÚBLICO",
        "Nenhum dado pessoal identificado",
        1.0
    )
