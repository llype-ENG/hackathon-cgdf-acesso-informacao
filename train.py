import pandas as pd
import joblib
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


#NTLK importar quando chegar em casa e finalizar
# 1. Carrega dataset
df = pd.read_excel("AMOSTRA_e-SIC.xlsx")

# 2. Texto
X = df["Texto Mascarado"].astype(str)

# 3. Função de bootstrap para rotulagem de CONTEXTO
def definir_contexto(texto: str) -> int:
    texto = texto.lower()

    # 1 = INTERESSE PESSOAL
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
        r"\breferente ao meu\b"
    ]

    for p in sinais_pessoais:
        if re.search(p, texto):
            return 1

    # 2 = CONTEXTO AMBÍGUO
    sinais_ambiguos = [
        r"\benvolve meu nome\b",
        r"\bconsta meu nome\b",
        r"\brespons[aá]vel pelo processo\b",
        r"\bna qualidade de representante\b",
        r"\brepresentante legal\b",
        r"\bbenefici[aá]rio\b"
    ]

    for p in sinais_ambiguos:
        if re.search(p, texto):
            return 2

    # 0 = NEUTRO / INSTITUCIONAL
    return 0

# 4. Geração automática do rótulo
df["context_label"] = X.apply(definir_contexto)
y = df["context_label"]

# 5. Vetorização
vectorizer = TfidfVectorizer(
    max_features=4000,
    ngram_range=(1, 2),
)

X_vec = vectorizer.fit_transform(X)

# 6. Modelo

model = LogisticRegression(
    max_iter=2000
)

model.fit(X_vec, y)

# 7. Salva modelo
joblib.dump(model, "context_model.pkl")
joblib.dump(vectorizer, "context_vectorizer.pkl")

print("✅ Modelo de CONTEXTO treinado e salvo com sucesso")
