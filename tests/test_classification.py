import os
import sys
import tempfile
import types
import unittest

from app.application.classification_service import ClassificationService
from app.domain.regex_personal_data_rule import RegexPersonalDataRule
from app.infrastructure.excel_repository import ExcelClassificationRepository
from services.classifier import classify
from services.regex_service import detect_regex


class FakeDataFrame:
    def __init__(self, rows):
        self._rows = rows
        self.columns = list(rows[0].keys()) if rows else []

    def iterrows(self):
        for index, row in enumerate(self._rows):
            yield index, row

    def to_excel(self, path, index=False):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("ok")


class PandasStub(types.ModuleType):
    def __init__(self):
        super().__init__("pandas")
        self.DataFrame = FakeDataFrame

    def read_excel(self, path):
        return FakeDataFrame(
            [
                {"ID": 1, "Texto Mascarado": "Solicitação sobre contratação pública."},
                {"ID": 2, "Texto Mascarado": "Meu nome é Ana e meu CPF é 123.456.789-09."},
            ]
        )


sys.modules.setdefault("pandas", PandasStub())


class RegexDetectionTests(unittest.TestCase):
    def test_detects_email(self):
        result = detect_regex("Contato: maria.silva@email.com")
        self.assertTrue(result["has_personal_data"])
        self.assertIn("EMAIL", result["matches"])

    def test_detects_name_pattern(self):
        result = detect_regex("Prezados, meu nome é Ana Maria Silva.")
        self.assertTrue(result["has_personal_data"])
        self.assertIn("NAME", result["matches"])


class ClassificationTests(unittest.TestCase):
    def test_public_text_is_allowed(self):
        service = ClassificationService(rules=[RegexPersonalDataRule()])
        result = service.classify("Solicitação sobre prestação de contas públicas.")
        self.assertEqual(result["classification"], "PÚBLICO")

    def test_private_text_is_blocked(self):
        result = classify("Meu nome é Ana e meu CPF é 123.456.789-09.")
        self.assertEqual(result["classification"], "NÃO PÚBLICO")
        self.assertEqual(result["reason"], "Dados pessoais explícitos")

    def test_processar_planilha_exports_results(self):
        repository = ExcelClassificationRepository(classification_service=ClassificationService(rules=[RegexPersonalDataRule()]))

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "entrada.xlsx")
            output_path = os.path.join(temp_dir, "saida.xlsx")
            with open(source_path, "wb") as handle:
                handle.write(b"fake")

            result = repository.processar_planilha(source_path, output_path)

            self.assertEqual(len(result._rows), 2)
            self.assertEqual(result._rows[0]["classificacao"], "PÚBLICO")
            self.assertEqual(result._rows[1]["classificacao"], "NÃO PÚBLICO")
            self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()
