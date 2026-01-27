import pandas as pd
from services.classifier import classify

def processar_planilha(caminho):
    df = pd.read_excel(caminho)
    resultados = []

    for _, row in df.iterrows():
        texto_original = row["Texto Mascarado"]

        # Apenas chama classify com o texto original
        resultado = classify(texto_original)

        resultados.append({
            "id": row["ID"],
            "texto": texto_original,
            "classificacao": resultado["classification"],
            "motivo": resultado["reason"],
            "confidence": resultado["confidence"]
        })

    df_saida = pd.DataFrame(resultados)
    df_saida.to_excel("resultado_classificacao.xlsx", index=False)
    return df_saida


# 47 62  76 87 90