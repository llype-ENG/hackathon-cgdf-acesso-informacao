# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Tuple, List, Optional, Dict, Any

try:
    import spacy
    _NLP_PT = spacy.load("pt_core_news_sm")
except Exception:
    _NLP_PT = None  # fallback sem NER

from services.regex_service import RegexService


class ClassificationService:
    """
    Classificação (PÚBLICO / NÃO PÚBLICO / REAVALIAÇÃO HUMANA)
    usando RegexService e, opcionalmente, SpaCy (se disponível).
    """

    EXPLICIT_TYPES = {"CPF", "RG", "EMAIL", "PHONE", "MATRICULA"}

    PERSONAL_TRIGGERS = [
        "me chamo", "meu nome é","Meu nome é"
        "sou ", "fui ", "trabalhei", "necessito",
        "solicitei", "recebi", "bolsa", "vaga de emprego",
        "meu imóvel", "minha casa", "minha residência", "meu endereço",
        "onde moro", "onde resido"
    ]

    _ME_CHAMO_REGEX = re.compile(
        r"(?i)\bme\s+chamo\s+("
        r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+"
        r"(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){0,4}"
        r")"
    )

    def __init__(self, regex_service: RegexService | None = None, nlp=None):
        self.regex_service = regex_service or RegexService()
        self._nlp = nlp if nlp is not None else _NLP_PT

    @staticmethod
    def _normalize(s: str) -> str:
        if not s:
            return ""
        return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()

    @classmethod
    def has_personal_context(cls, text: str) -> bool:
        tl = text.lower() if text else ""
        return any(t in tl for t in cls.PERSONAL_TRIGGERS)

    @classmethod
    def extract_name_after_me_chamo(cls, text: str) -> Optional[str]:
        if not text:
            return None
        m = cls._ME_CHAMO_REGEX.search(text)
        return cls._normalize(m.group(1)) if m else None

    def _extract_spacy_entities(self, text: str) -> Tuple[List[str], List[str]]:
        if not self._nlp or not text:
            return [], []
        doc = self._nlp(text)
        persons = list({ent.text.strip() for ent in doc.ents if ent.label_ in ("PER", "PERSON")})
        orgs = list({ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"})
        return persons, orgs

    @staticmethod
    def _build_result(classification: str, reason: str, confidence: float) -> Dict[str, Any]:
        return {
            "classification": classification,
            "reason": reason,
            "confidence": round(float(confidence), 2),
        }

    def classify(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return self._build_result("PÚBLICO", "Texto vazio", 1.0)

        # Regex
        rx = self.regex_service.detect(text)
        explicit = rx["explicit"]
        signature = rx["signature"]
        signature_name = rx["signature_name"]

        # 1) Assinatura ⇒ sempre NÃO PÚBLICO
        if signature and signature_name:
            return self._build_result(
                "NÃO PÚBLICO",
                f"Nome humano em assinatura: {signature_name}",
                0.95
            )

        # 2) Dados explícitos (ADDRESS depende de contexto)
        for m in explicit:
            t = m.get("type")
            if t == "ADDRESS":
                if self.has_personal_context(text):
                    return self._build_result("NÃO PÚBLICO", "Endereço pessoal identificado", 0.99)
                else:
                    continue
            if t in self.EXPLICIT_TYPES:
                return self._build_result("NÃO PÚBLICO", f"Dado pessoal explícito: {t}", 0.99)

        # 3) "Me chamo …"
        me_chamo_name = self.extract_name_after_me_chamo(text)
        if me_chamo_name:
            return self._build_result(
                "NÃO PÚBLICO",
                f"Nome humano em contexto pessoal direto (me chamo): {me_chamo_name}",
                0.99
            )

        # 4) NER (SpaCy)
        spacy_persons, spacy_orgs = self._extract_spacy_entities(text)
        if spacy_persons:
            if self.has_personal_context(text):
                return self._build_result(
                    "NÃO PÚBLICO",
                    f"Nome humano em contexto pessoal: {spacy_persons}",
                    0.98
                )
            return self._build_result(
                "REAVALIAÇÃO HUMANA",
                f"Nome humano sem contexto pessoal explícito: {spacy_persons}",
                0.75
            )

        # 5) Apenas entidades institucionais
        if spacy_orgs and not spacy_persons:
            return self._build_result(
                "PÚBLICO",
                "Texto com entidades institucionais apenas",
                0.95
            )

        # 6) Limpo
        return self._build_result(
            "PÚBLICO",
            "Nenhum dado pessoal identificado",
            1.0
        )


# Wrapper opcional (compatibilidade com from services.classifier import classify)
def classify(text: str):
    svc = ClassificationService()
    return svc.classify(text)
