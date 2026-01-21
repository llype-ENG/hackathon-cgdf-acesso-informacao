import pandas as pd
from services.classifier import classify

def processar_planilha(caminho):
    df = pd.read_excel(caminho)

    resultados = []

    for _, row in df.iterrows():
        texto = row["Texto Mascarado"]

        resultado = classify(texto)

        resultados.append({
            "id": row["ID"],
            "texto": texto,
            "classificacao": resultado["classification"],
            "motivo": resultado["reason"],
            "confidence": resultado["confidence"]
        })

    df_saida = pd.DataFrame(resultados)
    df_saida.to_excel("resultado_classificacao.xlsx", index=False)

    return df_saida
