from app.infrastructure.excel_repository import ExcelClassificationRepository

_repository = ExcelClassificationRepository()


def processar_planilha(caminho: str, destino: str | None = None):
    return _repository.processar_planilha(caminho, destino)
