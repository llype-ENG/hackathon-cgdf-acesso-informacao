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
            r"""
            (?<![A-Za-z0-9/])
            (?:\+55\s*)?
            (?:\(?[1-9][1-9]\)?)(?:[\s-]+)    # exige separador após o DDD
            (?:9?\d{4})
            [-\s]?
            \d{4}
            (?![A-Za-z0-9/])
            """,
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
            r'(?:Rua|R\.|Avenida|Av\.|Travessa|Tv\.|Alameda|Largo|Praça|Rodovia|Estrada|'
            r'Quadra|Qd\.|SQN|SQS|CLN|CLS|CRN|SCRN|SGAN|SGAS|SHIS|SHIG|SHIN|SHCN|'
            r'QE|QI|QL|QN|QS|CNB|CNA|CND|CSE|CSA|CSW|CSG|CSB|CSL|SCN|SCS)'
            r'\s+[A-Za-zÀ-ÿ0-9\-\/\.ºª]+'
            r'(?:\s*(?:–|-|,)\s*[A-Za-zÀ-ÿ0-9\-\/\.ºª]+)*'
            r'(?:\s+(?:Bloco|Bl\.|Lote|Lt\.|Casa|Apto\.?|Apartamento|Loja|Lj\.|Conjunto|CJ|CJ\.)\s*[A-Za-z0-9\-\/\.ºª]+)*'
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
            (atenciosamente|att\.?,?|cordialmente|grata)
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

        self.SIGNATURE_SIMPLE_REGEX = re.compile(
            r'''
            (?:\n|\.|,|\!|\?|(?:agradeç[o|a]|obrigad[o|a]))\s*   # fim de frase OU marcadores naturais de encerramento
            ([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+
                (?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){1,4}   # nome completo
            )
            (?:\s+(?:OAB\/[A-Z]{2}-\d+|CPF\s*\d{3}\.?\d{3}\.?\d{3}-?\d{2}|Matrícula\s*\S+))?
            ''',
            re.IGNORECASE | re.VERBOSE
        )   

        self.SIGNATURE_TYPO_REGEX = re.compile(
            r'''
            (?i)                                # case-insensitive

            # Gatilhos de assinatura digitados correto ou errado
            (?:at\.?te|att|atenciosamente|agrade[cç]o|obrigad[ao])

            \s*                                  # espaços opcionais

            # Nome grudado OU nome em linha seguinte
            (?:\n\s*|)                           # quebra ou nada

            # CAPTURA DO NOME COM OU SEM ERRO DE DIGITAÇÃO
            ([A-ZÁÉÍÓÚÂÊÔÃÕÇ]
                [a-záéíóúâêôãõç]+                # começa como nome
                (?:                              # grupo para sobrenomes OU sujeira grudada
                    \s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+
                    |                            # OU situações de erro:
                    [A-Za-záéíóúâêôãõç]{1,10}     # sufixo grudado: "GustavoConsegue"
                )*
            )
            ''',
            re.VERBOSE
        )

        self.ADDRESS_REGEX = re.compile(
            r'\b('
            r'(?:Rua|R\.|Avenida|Av\.|Travessa|Tv\.|Alameda|Largo|Praça|Rodovia|Estrada|'
            r'Quadra|Qd\.|SQN|SQS|CLN|CLS|CRN|SCRN|SGAN|SGAS|SHIS|SHIG|SHIN|SHCN|'
            r'QE|QI|QL|QN|QS|CNB|CNA|CND|CSE|CSA|CSW|CSG|CSB|CSL|ST|SCN|SCS)'
            r'\s+[A-Za-zÀ-ÿ0-9\-\/\.ºª]+'
            r'(?:\s*(?:–|-|,)\s*[A-Za-zÀ-ÿ0-9\-\/\.ºª]+)*'
            r'(?:\s+(?:Bloco|Bl\.|Lote|Lt\.|Casa|Apto\.?|Apartamento|Loja|Lj\.|Conjunto|CJ|CJ\.)\s*[A-Za-z0-9\-\/\.ºª]+)*'
            r')\b',
            re.IGNORECASE
        )

        self.ADDRESS_CEP_REGEX = re.compile(
            r'(?P<addr>'
            r'(?:[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\./ºª\-–,]{5,120}?)'   # trecho de endereço “livre”
            r')\s*,?\s*CEP\s*\d{5}\s*[-–]\s*\d{3}\b',
            re.IGNORECASE
        )

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

        # ... loop que coleta EMAIL, CPF, RG, MATRICULA, ADDRESS, PHONE ...

        # Captura adicional por CEP
        for m in self.ADDRESS_CEP_REGEX.finditer(text):
            cep_match = re.search(r'CEP\s*\d{5}\s*[-–]\s*\d{3}\b', m.group(0), re.IGNORECASE)
            addr = m.group('addr').strip(' ,.;:-–')
            explicit.append({
                "type": "ADDRESS",
                "value": f"{addr}, {cep_match.group(0)}" if cep_match else addr,
                "start": m.start()
            })
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
        
        
        if not signature_match:
            typo_sig = self.SIGNATURE_TYPO_REGEX.search(text)
            if typo_sig:
                signature_match = typo_sig

        
        # NOVO: se não encontrou assinatura clássica, tenta assinatura simples
        if not signature_match:
            simple_sig = self.SIGNATURE_SIMPLE_REGEX.search(text)
            if simple_sig:
                signature_match = simple_sig


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
