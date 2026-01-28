# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List, Tuple, Optional


class RegexService:
    """
    Serviço de regex para detecção de dados explícitos, nomes e assinatura.
    Ajustado para reduzir falsos positivos em 'assinatura'.
    """

    def __init__(self):
        # =========================
        # DADOS EXPLÍCITOS
        # =========================
        self.CPF_REGEX = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")

        self.EMAIL_REGEX = re.compile(
            r"\b[\w.\-+]+@[\w.\-]+\.\w{2,}\b",
            re.IGNORECASE,
        )

        self.PHONE_REGEX = re.compile(
            r"""
            (?<![A-Za-z0-9/])           # não colado à esquerda
            (?:\+55\s*)?                 # opcional +55
            (?:\(?[1-9][1-9]\)?)(?:[\s-]+) # DDD com separador obrigatório
            (?:9?\d{4})                  # prefixo (pode ter 9)
            [-\s]?                       # separador opcional
            \d{4}                        # sufixo
            (?![A-Za-z0-9/])             # não colado à direita
            """,
            re.VERBOSE,
        )

        self.SEI_REGEX = re.compile(
            r"\bSEI[:\s]*\d{4,6}-\d{7,8}/\d{4}-\d{2}\b",
            re.IGNORECASE,
        )

        self.RG_REGEX = re.compile(
            r"""\b(?:RG|Registro\s+Geral)\s*[:\-]?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[A-Za-z0-9]\b""",
            re.IGNORECASE,
        )

        self.MATRICULA_REGEX = re.compile(
            r"""\bMATR[IÍ]CULA\s*[:\-]?\s*[\d.\-]{4,15}\b""",
            re.IGNORECASE,
        )

        self.ADDRESS_REGEX = re.compile(
            r"""
            \b(
              (?:Rua|R\.|Avenida|Av\.|Travessa|Tv\.|Alameda|Largo|Praça|Rodovia|Estrada|
               Quadra|Qd\.|SQN|SQS|CLN|CLS|CRN|SCRN|SGAN|SGAS|SHIS|SHIG|SHIN|SHCN|
               QE|QI|QL|QN|QS|CNB|CNA|CND|CSE|CSA|CSW|CSG|CSB|CSL|SCN|SCS|ST)
              \s+[A-Za-zÀ-ÿ0-9\-/.\º\ª]+
              (?:\s*(?:\u2013|-|,)\s*[A-Za-zÀ-ÿ0-9\-/.\º\ª]+)*
              (?:\s+(?:Bloco|Bl\.|Lote|Lt\.|Casa|Apto\.?|Apartamento|Loja|Lj\.|Conjunto|CJ|CJ\.)\s*[A-Za-z0-9\-/.\º\ª]+)*
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        self.ADDRESS_CEP_REGEX = re.compile(
            r"(?P<addr>(?:[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s./ºª\-\u2013,]{5,120}?))\s*,?\s*CEP\s*\d{5}\s*[-\u2013]\s*\d{3}\b",
            re.IGNORECASE,
        )

        # =========================
        # NOMES
        # =========================
        self.NAME_TOKEN = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+"

        self.COMPOSED_NAME_REGEX = re.compile(
            rf"\b({self.NAME_TOKEN}(?:\s+{self.NAME_TOKEN}){{1,4}})\b"
        )

        # >>> CORRIGIDO: uma palavra capitalizada com pelo menos 3 letras
        self.SINGLE_NAME_REGEX = re.compile(
            r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,})\b"
        )

        # =========================
        # ASSINATURA — CONSTS/REGEX
        # =========================
        self.VALEDICTIONS = (
            r"(?:atenciosamente|att\.?|a?t\.?e\.?|cordialmente|respeitosamente|grato\.?|grata\.?)"
        )

        self.HUMAN_NAME = re.compile(
            rf"\b({self.NAME_TOKEN}(?:\s+{self.NAME_TOKEN}){{1,3}})\b"
        )

        # Stoplists
        self.SIGNATURE_HARD_STOP = {
            "att", "att.", "atenciosamente", "cordialmente", "respeitosamente",
            "abs", "obrigado", "obrigada", "grato", "grata"
        }
        self.SIGNATURE_CONTEXT_STOP = {
            # títulos/termos institucionais
            "Políticas", "Públicas", "Constituição", "Federal", "Site", "Google", "Maps",
            "Viabilidade", "Técnica", "Quantidade", "Processo", "Administrativo", "Dívida",
            "Atividade", "Defesa", "Consumidor", "Instituto", "Brasileiro", "Inteligência",
            "Artificial", "Letramento", "Demográfico", "Generativa", "Anexo", "Segue", "Porque",
            # topônimos/termos técnicos recorrentes no corpus
            "São", "Paulo", "Lago", "Norte", "Ribeirão", "Bananal", "Universidade", "Professor",
            "Recursos", "Hídricos", "Power", "Bi", "Clorofila-a", "Coliformes", "Termotolerantes",
            "Fósforo", "Nitrogênio", "Oxigênio", "Sólidos", "Temperatura", "Turbidez"
        }

        # Apenas a L I N H A de despedida (coletaremos as 1–3 linhas seguintes manualmente)
        self.SIGNATURE_BLOCK_REGEX = re.compile(
            rf"^\s*(?:{self.VALEDICTIONS})\s*[,:-]?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )

        # Padrões "soltos" — serão validados com heurística de rodapé + linha anterior
        self.SIGNATURE_SIMPLE_REGEX = re.compile(
            rf"""
            (?:[\.\,\!\?])\s*                                 # pontuação imediatamente antes
            ({self.NAME_TOKEN}(?:\s+{self.NAME_TOKEN}){{1,4}}) # nome completo (2-5 tokens)
            (?:\s+(?:OAB/[A-Z]{{2}}-\d+|CPF\s*\d{{3}}\.\d{{3}}\.\d{{3}}-?\d{{2}}|Matrícula\s*\S+))?
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        self.SIGNATURE_TYPO_REGEX = re.compile(
            rf"""
            (?:at\.?te|att|atenciosamente|grata|agrade[cç]o|obrigad[ao])\s* # gatilhos
            (?:\n\s*)?                                                # quebra opcional
            ({self.NAME_TOKEN}(?:\s+{self.NAME_TOKEN}){{1,4}})        # nome completo
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        self.PUBLIC_ENTITIES = {
            "Distrito Federal",
            "Governo do Distrito Federal",
            "GDF",
            "União",
            "Estado",
            "Município",
        }

    # =========================
    # NORMALIZAÇÃO
    # =========================
    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    # =========================
    # HELPERS — ASSINATURA
    # =========================
    @staticmethod
    def _is_in_tail_window(text: str, span: Tuple[int, int], lines_tail: int = 10) -> bool:
        """Verifica se o match está nas últimas N linhas do texto."""
        lines = text.splitlines()
        tail = "\n".join(lines[-lines_tail:]) if lines_tail > 0 else text
        start_base = len(text) - len(tail)
        return span[0] >= start_base

    def _has_valediction_above(self, text: str, start_idx: int) -> bool:
        """Verifica se há despedida/agradecimento na linha imediatamente anterior ao match."""
        head = text[:start_idx]
        lines = head.splitlines()
        if not lines:
            return False
        prev = lines[-1].strip()

        valediction_rx = re.compile(self.VALEDICTIONS, re.IGNORECASE)
        thanks_rx = re.compile(r"\b(obrigad[oa]|agrade[cç]o)\b", re.IGNORECASE)
        return bool(valediction_rx.search(prev) or thanks_rx.search(prev))

    def _pick_signature_name(self, sig_lines: List[str]) -> Optional[str]:
        """Escolhe o melhor candidato a nome dentre 1–3 linhas de assinatura."""
        for line in sig_lines:
            lstrip = line.strip()
            if not lstrip:
                continue
            if lstrip.lower() in self.SIGNATURE_HARD_STOP:
                continue

            m = self.HUMAN_NAME.search(lstrip)
            if not m:
                continue

            candidate = m.group(1).strip()
            tokens = candidate.split()
            if not (2 <= len(tokens) <= 4):
                continue
            if any(tok in self.SIGNATURE_CONTEXT_STOP for tok in tokens):
                continue

            return candidate
        return None

    def _extract_signature(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Estratégia:
        1) Procurar linha de despedida próxima ao fim e coletar até 3 linhas subsequentes.
        2) Fallback SIMPLE/TYPO apenas se houver valediction/agradecimento na linha anterior + janela final.
        """
        # 1) Valediction "real" (pega a última)
        last_m = None
        for m in self.SIGNATURE_BLOCK_REGEX.finditer(text):
            last_m = m
        if last_m:
            end = last_m.end()
            tail_lines = text[end:].splitlines()
            sig_lines: List[str] = []
            for ln in tail_lines[:3]:
                if ln.strip():
                    sig_lines.append(ln.strip())
            name = self._pick_signature_name(sig_lines)
            if name:
                return True, name

        # 2) Fallback (mais estrito)
        for rx in (self.SIGNATURE_TYPO_REGEX, self.SIGNATURE_SIMPLE_REGEX):
            m = rx.search(text)
            if not m:
                continue
            if not self._is_in_tail_window(text, m.span(), lines_tail=10):
                continue
            if not self._has_valediction_above(text, m.start()):
                continue

            rest = text[m.end():].strip()
            # Se houver texto "corridão" demais após o match, provavelmente não é assinatura
            if len(rest) > 140 and ("\n" not in rest or rest.index("\n") > 140):
                continue

            block = text[m.start():].splitlines()[:3]
            sig_lines = [ln.strip() for ln in block if ln.strip()]
            name = self._pick_signature_name(sig_lines)
            if name:
                return True, name

        return False, None

    # =========================
    # DETECT
    # =========================
    def detect(self, text: str) -> dict:
        """
        Retorna dicionário com:
          - explicit: lista de {type, value, start}
          - names:    lista de {type, value, start}
          - signature: bool
          - signature_name: str | None
        """
        if not text or not text.strip():
            return {
                "explicit": [],
                "names": [],
                "signature": False,
                "signature_name": None,
            }

        text = self.normalize(text)
        explicit = []
        names = []

        # Endereço por CEP
        for m in self.ADDRESS_CEP_REGEX.finditer(text):
            cep_match = re.search(r"CEP\s*\d{5}\s*[-\u2013]\s*\d{3}\b", m.group(0), re.IGNORECASE)
            addr = m.group("addr").strip(" ,.;:-\u2013")
            explicit.append({
                "type": "ADDRESS",
                "value": f"{addr}, {cep_match.group(0)}" if cep_match else addr,
                "start": m.start(),
            })

        # Processo SEI
        for m in self.SEI_REGEX.finditer(text):
            explicit.append({
                "type": "PROCESSO_SEI",
                "value": m.group(0),
                "start": m.start(),
            })

        # Demais dados explícitos
        for regex, dtype in [
            (self.EMAIL_REGEX, "EMAIL"),
            (self.CPF_REGEX, "CPF"),
            (self.RG_REGEX, "RG"),
            (self.MATRICULA_REGEX, "MATRICULA"),
            (self.ADDRESS_REGEX, "ADDRESS"),
            (self.PHONE_REGEX, "PHONE"),
        ]:
            for m in regex.finditer(text):
                explicit.append({
                    "type": dtype,
                    "value": m.group(0),
                    "start": m.start(),
                })

        # Nomes compostos no corpo (exclui entidades públicas)
        for m in self.COMPOSED_NAME_REGEX.finditer(text):
            value = m.group(1)
            if value not in self.PUBLIC_ENTITIES:
                names.append({
                    "type": "NAME",
                    "value": value,
                    "start": m.start(),
                })

        # Assinatura
        signature, signature_name = self._extract_signature(text)
        if signature and signature_name:
            names.append({
                "type": "NAME",
                "value": signature_name,
                "start": text.rfind(signature_name),
            })

        return {
            "explicit": explicit,
            "names": names,
            "signature": bool(signature),
            "signature_name": signature_name,
        }
