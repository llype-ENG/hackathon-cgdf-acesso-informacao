
import regex as re


# =========================
# REGEX BÁSICOS
# =========================
#57 #68
CPF_REGEX = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')

EMAIL_REGEX = re.compile(
    r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b',
    re.IGNORECASE
)

MATRICULA_REGEX = re.compile(
    r'\bMATR[IÍ]CULA\s*[:\-]?\s*\d{6,10}[A-Z]?\b',
    re.IGNORECASE
)

NAME_WITH_MATRICULA_REGEX = re.compile(
    r'\b([A-ZÁ-ÚÇ][a-zá-úç]+(?:\s+[A-ZÁ-ÚÇ][a-zá-úç]+)+)\s*-\s*MATR[IÍ]CULA\b',
    re.IGNORECASE
)

PROCESS_REGEX = re.compile(
    r'\b\d{4,6}-\d{6,8}/\d{4}-\d{2}\b'
)

RG_REGEX = re.compile(
    r'\b(?:RG|Registro\s+Geral)\s*[:\-]?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[A-Za-z0-9]\b',
    re.IGNORECASE
)

# =========================
# TELEFONE
# =========================

PHONE_REGEX = re.compile(
    r'(?<!\w)(?:\+55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}\b'
)

PHONE_BLOCK_CONTEXT_REGEX = re.compile(
    r'\b(SEI|processo|proc\.?|OAB|matr[ií]cula|autos|n[ºo])\b',
    re.IGNORECASE
)

PHONE_POSITIVE_CONTEXT_REGEX = re.compile(
    r'\b(tel\.?|telefone|whatsapp|contato|fone|cel\.?)\b',
    re.IGNORECASE
)

PHONE_NEGATIVE_PATTERN_REGEX = re.compile(
    r'^\d{2}-\d{4}-\d{4}$'
)

# =========================
# CONTEXTO DE NOME
# =========================

PJ_CONTEXT_REGEX = re.compile(
    r'\b(empresa|raz[aã]o social|pessoa jur[ií]dica|'
    r'LTDA|Ltda|S\/A|SA|EIRELI|ME|EPP|CNPJ)\b',
    re.IGNORECASE
)

INSTITUTIONAL_CONTEXT_REGEX = re.compile(
    r'\b(orientador(a)?|pesquisador(a)?|professor(a)?|'
    r'doutor(a)?|servidor(a)?|cargo|fun[cç][aã]o|'
    r'secret[aá]rio(a)?|diretor(a)?)\b',
    re.IGNORECASE
)

# =========================
# NOME
# =========================

NAME_INLINE_SIGNATURE_REGEX = re.compile(
    r'\b(agrade[cç]o|agradecemos|atenciosamente|cordialmente)\b'
    r'[\s,.:;-]+'
    r'([A-ZÁ-Ú][a-zá-ú]+(?:\s+[A-ZÁ-Ú][a-zá-ú]+){1,3})'
    r'(?:\s+\b(OAB|CPF|RG|SEI|processo)\b|$)',
    re.IGNORECASE
)


NAME_SIGNATURE_REGEX = re.compile(
    r'\b('
    r'meu nome é|me chamo|assinado por|'
    r'atenciosamente|att\.?|at\.?te\.?|'
    r'cordialmente|sds\.?|abs\.?'
    r')\b'
    r'[\s\.,:;-]*'
    r'[\p{Lu}][\p{Ll}]+'
    r'(?:\s+[\p{Lu}][\p{Ll}]+){0,3}',
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)


NAME_FINAL_SIGNATURE_REGEX = re.compile(
    r'(?:\n|\r|\A)\s*'
    r'([A-ZÁ-Ú][a-zá-ú]+(?:\s+[A-ZÁ-Ú][a-zá-ú]+){1,3})'
    r'\s*(?:\n|\r|\Z)',
    re.MULTILINE
)

NAME_CANDIDATE_REGEX = re.compile(
    r'\b[A-ZÁ-Ú][a-zá-ú]+(?:\s+[A-ZÁ-Ú][a-zá-ú]+){1,3}\b'
)

PHONE_HARD_BLOCK_CONTEXT_REGEX = re.compile(
    r'\b(nire|protocolo|viabilidade|junta|taxa|dfp)\b',
    re.IGNORECASE
)


# =========================
# FUNÇÕES AUXILIARES
# =========================

def is_valid_phone_number(match: str) -> bool:
    number = re.sub(r'\D', '', match)

    if not (8 <= len(number) <= 11):
        return False

    if number.startswith('0'):
        return False

    if len(set(number)) <= 2:
        return False

    return True



def has_blocked_phone_context(text, start, end) -> bool:
    window = text[max(0, start - 15):min(len(text), end + 15)]

    
    if PROCESS_REGEX.search(window):
        # bloqueia apenas se o match de processo SOBREPOR o telefone
        proc_match = PROCESS_REGEX.search(window)
        if proc_match.start() <= (end - start) <= proc_match.end():
            return True


    if re.search(r'\b(OAB|MATR[IÍ]CULA|AUTOS)\b', window, re.IGNORECASE):
        return True

    return False



# =========================
# DETECÇÃO PRINCIPAL
# =========================

def detect_regex(text: str) -> dict:
    if not isinstance(text, str) or not text:
        return {
            "has_personal_data": False,
            "matches": [],
            "ignored": []
        }

    text = text.replace('\xa0', ' ').strip()
    matches = []
    ignored = []

    if EMAIL_REGEX.search(text):
        matches.append("EMAIL")

    if CPF_REGEX.search(text):
        matches.append("CPF")

    if RG_REGEX.search(text):
        matches.append("RG")
    
    # Matrícula funcional → dado pessoal
    if MATRICULA_REGEX.search(text):
        matches.append("MATRICULA")

    # Nome associado à matrícula → dado pessoal
    if NAME_WITH_MATRICULA_REGEX.search(text):
        if "NAME" not in matches:
            matches.append("NAME")

    
    phone_match = PHONE_REGEX.search(text)


    if phone_match:
        raw_phone = phone_match.group()

        strong_format = is_strong_phone_format(raw_phone)
        has_positive_context = bool(PHONE_POSITIVE_CONTEXT_REGEX.search(text))
        has_hard_block = bool(PHONE_HARD_BLOCK_CONTEXT_REGEX.search(text))
        is_negative_pattern = bool(PHONE_NEGATIVE_PATTERN_REGEX.match(raw_phone))

        if (
            is_valid_phone_number(raw_phone)
            and not has_blocked_phone_context(text, phone_match.start(), phone_match.end())
            and not is_negative_pattern
            and not has_hard_block
            and (strong_format or has_positive_context)
        ):
            matches.append("PHONE")


    if NAME_SIGNATURE_REGEX.search(text):
        matches.append("NAME")

    elif NAME_FINAL_SIGNATURE_REGEX.search(text):
        matches.append("NAME")
    
    elif NAME_INLINE_SIGNATURE_REGEX.search(text):
        matches.append("NAME")

    
    elif NAME_CANDIDATE_REGEX.search(text):

        if CPF_REGEX.search(text) and name_near_cpf(text):
            matches.append("NAME")

        elif PJ_CONTEXT_REGEX.search(text):
            ignored.append({
                "type": "NAME",
                "reason": "Nome identificado integra razão social de pessoa jurídica"
            })

        elif INSTITUTIONAL_CONTEXT_REGEX.search(text):
            ignored.append({
                "type": "NAME",
                "reason": "Nome identificado em contexto institucional"
            })


    return {
        "has_personal_data": len(matches) > 0,
        "matches": matches,
        "ignored": ignored
    }


def name_near_cpf(text: str) -> bool:
    return bool(
        re.search(
            r'\bCPF\b.{0,60}[A-ZÁ-ÚÇ][a-zá-úç]+(?:\s+[A-ZÁ-ÚÇ][a-zá-úç]+)+',
            text,
            re.IGNORECASE
        ) or
        re.search(
            r'[A-ZÁ-ÚÇ][a-zá-úç]+(?:\s+[A-ZÁ-ÚÇ][a-zá-úç]+)+.{0,60}\bCPF\b',
            text,
            re.IGNORECASE
        )
    )



def is_strong_phone_format(raw: str) -> bool:
    clean = re.sub(r'\D', '', raw)

    # Formato forte:
    # - tem DDD entre parênteses
    # - tem +55
    # - começa com 6–9 após limpeza (celulares BR)
    return (
        raw.strip().startswith('(') or
        raw.strip().startswith('+55') or
        (len(clean) >= 9 and clean[0] in '6789')
    )



