
import re

def definir_contexto(texto: str) -> int:
    texto = texto.lower()

    # 0 = NEUTRO / INSTITUCIONAL
    # 1 = INTERESSE PESSOAL CLARO
    # 2 = CONTEXTO AMBÍGUO

    # ===== INTERESSE PESSOAL CLARO =====
    sinais_institucionais = [
    r"programa de integridade",
    r"unidade responsável",
    r"diretrizes",
    r"controle interno",
    r"plano de integridade",
    r"alta administração",
    r"política de gestão de riscos",
    r"órgão/entidade",
    r"ministerio|secretaria|prefeitura|governo"
    ]

    for padrao in sinais_institucionais:
        if re.search(padrao, texto):
            return 0  # força NEUTRO

    sinais_pessoais = [
        r"\bmeu processo\b",
        r"\bmeus dados\b",
        r"\bmeu nome\b",
        r"\bem meu nome\b",
        r"\bsou o interessado\b",
        r"\bsou a interessada\b",
        r"\bsou o requerente\b",
        r"\bsou a requerente\b",
        r"\bn[aã]o consigo acesso\b",
        r"\bn[aã]o tive acesso\b",
        r"\bsolicito acesso ao meu\b",
        r"\bsolicito acesso em meu nome\b",
        r"\brequerente\b",
        r"\binteressado\b",
        r"\breferente ao meu\b"
    ]

    for padrao in sinais_pessoais:
        if re.search(padrao, texto):
            return 1  # INTERESSE PESSOAL

    # ===== CONTEXTO AMBÍGUO =====
    sinais_ambiguos = [
        r"\benvolve meu nome\b",
        r"\bconsta meu nome\b",
        r"\brelacionado ao meu nome\b",
        r"\brespons[aá]vel pelo processo\b",
        r"\bunico respons[aá]vel\b",
        r"\bna qualidade de representante\b",
        r"\bcomo representante\b",
        r"\brepresentante legal\b",
        r"\brespons[aá]vel legal\b",
        r"\bdemanda pessoal\b",
        r"\binteresse particular\b",
        r"\bprocesso individual\b",
        r"\bbenefici[aá]rio\b"
    ]

    for padrao in sinais_ambiguos:
        if re.search(padrao, texto):
            return 2  # AMBÍGUO

    # ===== NEUTRO / INSTITUCIONAL =====
    return 0
