import pandas as pd
import joblib
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# =========================
# 1️⃣ Carrega dataset
# =========================
df = pd.read_excel("AMOSTRA_e-SIC.xlsx")  # coluna: "Texto Mascarado"
X = df["Texto Mascarado"].astype(str)


nltk.download("stopwords")
stopwords_pt = stopwords.words("portuguese")

# =========================
# 2️⃣ Função de bootstrap para rotulagem
# =========================
def definir_contexto(texto: str) -> int:
    texto_lower = texto.lower()

    # ===== INTERESSE PESSOAL CLARO =====
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
        r"\breferente ao meu\b",
        r"\bme chamo\b",
        r"\bvenho requerer\b",
        r"\ba meu respeito\b",
        r"\bsolicito informações sobre mim\b",
        r"\bqueria informações sobre mim\b",
        r"\bsou titular\b",
        r"\bme identifico como\b",
        r"\bmeu registro\b",
        r"\bmeu protocolo\b",
        r"\bmeu cpf\b",
        r"\bmeu rg\b"
    ]
    for p in sinais_pessoais:
        if re.search(p, texto_lower):
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
        r"\bbenefici[aá]rio\b",
        r"\bmandato\b",
        r"\bprocurador\b",
        r"\badvogado de\b",
        r"\bautorizado por\b"
    ]
    for p in sinais_ambiguos:
        if re.search(p, texto_lower):
            return 2  # AMBÍGUO

    # ===== NEUTRO / INSTITUCIONAL =====
    sinais_institucionais = [
        r"programa de integridade",
        r"unidade responsável",
        r"diretrizes",
        r"controle interno",
        r"plano de integridade",
        r"alta administração",
        r"política de gestão de riscos",
        r"órgão/entidade",
        r"ministerio|secretaria|prefeitura|governo",
        r"indicadores de desempenho",
        r"capacitação de pessoal",
        r"relatório anual",
        r"legislação",
        r"normativo",
        r"procedimento interno",
        r"gestão de riscos",
        r"programas públicos",
        r"instituto|fundação",
        r"conselho|comissão|diretoria"
    ]
    for p in sinais_institucionais:
        if re.search(p, texto_lower):
            return 0  # NEUTRO

    return 0  # padrão

# =========================
# 3️⃣ Geração automática do rótulo
# =========================
df["context_label"] = X.apply(definir_contexto)
y = df["context_label"]

# =========================
# 4️⃣ Vetorização TF-IDF
# =========================
vectorizer = TfidfVectorizer(
    max_features=6000,
    ngram_range=(1, 2),
    stop_words=stopwords_pt
)
X_vec = vectorizer.fit_transform(X)

# =========================
# 5️⃣ Modelo
# =========================
model = LogisticRegression(max_iter=3000)
model.fit(X_vec, y)

# =========================
# 6️⃣ Salva modelo e vectorizer
# =========================
joblib.dump(model, "context_model.pkl")
joblib.dump(vectorizer, "context_vectorizer.pkl")

print("✅ Modelo de CONTEXTO treinado com bootstrap amplo e salvo com sucesso")
