import regex as re


class RegexService:
    def __init__(self):
        # =========================
        # DADOS EXPLÍCITOS
        # =========================
        self.CPF_REGEX = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')

        self.SIGNATURE_STOPWORDS = {
            "att", "att.", "atenciosamente", "cordialmente",
            "respeitosamente", "abs", "obrigado", "obrigada"
        }

        self.EMAIL_REGEX = re.compile(
            r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b',
            re.IGNORECASE
        )

        self.PHONE_REGEX = re.compile(
            r'''
            (?<!\d)
            (?:\+55\s*)?
            (?:\(?\d{2}\)?\s*)
            (?:9?\d{4})
            [-\s]?
            \d{4}
            (?![\d\/\-])
            ''',
            re.VERBOSE
        )

        self.SEI_REGEX = re.compile(
            r'\bSEI[:\s]*\d{4,6}-\d{7,8}\/\d{4}-\d{2}\b',
            re.IGNORECASE
        )

        self.RG_REGEX = re.compile(
            r'\b(?:RG|Registro\s+Geral)\s*[:\-]?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[A-Za-z0-9]\b',
            re.IGNORECASE
        )

        self.MATRICULA_REGEX = re.compile(
            r'\bMATR[IÍ]CULA\s*[:\-]?\s*[\d\.\-]{4,15}\b',
            re.IGNORECASE
        )

        self.ADDRESS_REGEX = re.compile(
            r'\b('
            r'(?:Rua|R\.|Avenida|Av\.|Travessa|Tv\.|Quadra|Qd\.|Setor|SR|SQ|CRN|CL[NS]|SCRN|SQS)'
            r'\s+[A-Z0-9]+'
            r'(?:\s*[–\-]\s*[A-Z0-9]+)?'
            r'(?:\s+(?:Bloco|Bl\.|Lote|Lt\.|Loja|Lj\.)\s*[A-Z0-9]+)*'
            r')\b',
            re.IGNORECASE
        )

        # =========================
        # NOMES
        # =========================

        # Nome composto (2 a 5 palavras)
        self.COMPOSED_NAME_REGEX = re.compile(
            r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+'
            r'(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){1,4})\b'
        )

        # Nome simples (1 palavra)
        self.SINGLE_NAME_REGEX = re.compile(
            r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,})\b'
        )

        # =========================
        # ASSINATURA (BLOCO)
        # =========================
        self.SIGNATURE_BLOCK_REGEX = re.compile(
            r'''
            (atenciosamente|att\.?,?|cordialmente)
            [\s,]*
            (
                (?:\n|\r|\s)+
                [^\n\r]{2,100}
                (?:
                    (?:\n|\r)[^\n\r]{2,100}
                ){0,4}
            )
            ''',
            re.IGNORECASE | re.VERBOSE
        )

        self.PUBLIC_ENTITIES = {
            "Distrito Federal",
            "Governo do Distrito Federal",
            "GDF",
            "União",
            "Estado",
            "Município"
        }

    # =========================
    # NORMALIZAÇÃO
    # =========================
    @staticmethod
    def normalize(text: str) -> str:
        text = text.replace('\xa0', ' ')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        return text.strip()

    # =========================
    # DETECT
    # =========================
    def detect(self, text: str) -> dict:
        if not text or not text.strip():
            return {
                "explicit": [],
                "names": [],
                "signature": False,
                "signature_name": None
            }

        text = self.normalize(text)

        explicit = []
        names = []

        # =========================
        # PROCESSO SEI
        # =========================
        for m in self.SEI_REGEX.finditer(text):
            explicit.append({
                "type": "PROCESSO_SEI",
                "value": m.group(),
                "start": m.start()
            })

        # =========================
        # DADOS EXPLÍCITOS
        # =========================
        for regex, dtype in [
            (self.EMAIL_REGEX, "EMAIL"),
            (self.CPF_REGEX, "CPF"),
            (self.RG_REGEX, "RG"),
            (self.MATRICULA_REGEX, "MATRICULA"),
            (self.ADDRESS_REGEX, "ADDRESS"),
            (self.PHONE_REGEX, "PHONE")
        ]:
            for m in regex.finditer(text):
                explicit.append({
                    "type": dtype,
                    "value": m.group(),
                    "start": m.start()
                })

        # =========================
        # NOMES COMPOSTOS (CORPO)
        # =========================
        for m in self.COMPOSED_NAME_REGEX.finditer(text):
            if m.group() not in self.PUBLIC_ENTITIES:
                names.append({
                    "type": "NAME",
                    "value": m.group(),
                    "start": m.start()
                })

        # =========================
        # ASSINATURA
        # =========================
        signature_match = self.SIGNATURE_BLOCK_REGEX.search(text)
        signature_name = None

        if signature_match:
            signature_block = signature_match.group(0)

            # tenta nome composto primeiro
            composed = self.COMPOSED_NAME_REGEX.search(signature_block)
            if composed:
                candidate = composed.group(1)
                if candidate.lower() not in self.SIGNATURE_STOPWORDS:
                    signature_name = candidate
            else:
                # tenta todos os nomes simples e pega o ÚLTIMO válido
                simples = self.SINGLE_NAME_REGEX.findall(signature_block)
                for s in reversed(simples):
                    if s.lower() not in self.SIGNATURE_STOPWORDS:
                        signature_name = s
                        break


            if signature_name:
                names.append({
                    "type": "NAME",
                    "value": signature_name,
                    "start": text.rfind(signature_name)
                })

        return {
            "explicit": explicit,
            "names": names,
            "signature": bool(signature_match),
            "signature_name": signature_name
        }
