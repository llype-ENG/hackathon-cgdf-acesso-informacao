from pathlib import Path

from app.application.classification_service import ClassificationService


class ExcelClassificationRepository:
    def __init__(self, classification_service: ClassificationService | None = None):
        self.classification_service = classification_service or ClassificationService()

    def processar_planilha(self, caminho: str, destino: str | None = None):
        import pandas as pd

        source_path = Path(caminho)
        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        dataframe = pd.read_excel(source_path)
        if "Texto Mascarado" not in dataframe.columns:
            raise ValueError("A planilha precisa conter a coluna 'Texto Mascarado'.")

        resultados = []
        for _, row in dataframe.iterrows():
            texto = str(row.get("Texto Mascarado", ""))
            resultado = self.classification_service.classify(texto)
            resultados.append(
                {
                    "id": row.get("ID"),
                    "texto": texto,
                    "classificacao": resultado["classification"],
                    "motivo": resultado["reason"],
                    "confidence": resultado.get("confidence", 0.0),
                }
            )

        saida = pd.DataFrame(resultados)
        output_path = Path(destino) if destino else Path("resultado_classificacao.xlsx")
        saida.to_excel(output_path, index=False)
        return saida
