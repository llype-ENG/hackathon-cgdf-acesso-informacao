import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

df = pd.read_excel("AMOSTRA_e-SIC.xlsx")

X = df["Texto Mascarado"].astype(str)

df["label"] = df["Texto Mascarado"].str.contains(
    r"cpf|rg|endereço|telefone|email|meu companheiro|minha esposa|minha filha|meu filho",
    case=False,
    na=False
).astype(int)

y = df["label"]

vectorizer = TfidfVectorizer(
    max_features=3000,
    ngram_range=(1, 2)
)


X_vec = vectorizer.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Modelo treinado e salvo com sucesso!")
