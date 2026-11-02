"""
BR-Access-NER — inferência e classificação binária de documentos.

Execução direta na raiz do projeto:
    python -u src/inference/predict.py

Entrada:
    AMOSTRA_e-SIC.xlsx
    Colunas: ID, Texto Mascarado

Saídas:
    reports/predictions/amostra_esic_99_classificacao.xlsx
    reports/predictions/amostra_esic_99_classificacao.csv
    reports/predictions/amostra_esic_99_classificacao_metadata.json

O modelo é um NER. A classe binária é derivada das entidades previstas:
- COM DADO PESSOAL: pelo menos uma entidade de uma das 11 classes PII.
- SEM DADO PESSOAL IDENTIFICADO: nenhuma entidade dessas classes foi prevista.

ORG_JURIDICA e DOC_EMPRESA, isoladamente, não contam como PII,
seguindo a definição adotada do dataset de origem.

A classificação é automática e não substitui revisão humana.
"""

import os

# Workaround para o carregamento de pesos identificado no Windows
# com o ambiente Transformers utilizado neste projeto.
os.environ["HF_DEACTIVATE_ASYNC_LOAD"] = "1"
os.environ["DISABLE_SAFETENSORS_CONVERSION"] = "1"

import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import torch
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from transformers import AutoModelForTokenClassification, AutoTokenizer


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = ROOT / "models" / "bertimbau_esic_ner"
INPUT_FILE = ROOT / "AMOSTRA_e-SIC.xlsx"
OUTPUT_DIR = ROOT / "reports" / "predictions"

MAX_LENGTH = 512
STRIDE = 64

CLASS_WITH_PII = "COM DADO PESSOAL"
CLASS_WITHOUT_DETECTED_PII = "SEM DADO PESSOAL IDENTIFICADO"

PII_ENTITY_TYPES = frozenset({
    "CONTATO",
    "DADO_FINANCEIRO",
    "DADO_SAUDE",
    "DATA_NASC",
    "DOC_PESSOAL",
    "DOC_PROFISSIONAL",
    "ENDERECO",
    "ID_PROCESSUAL",
    "ID_VEICULO",
    "NOME_PESSOA",
    "QUASI_IDENTIFICADOR",
})

NON_PII_ENTITY_TYPES = frozenset({
    "DOC_EMPRESA",
    "ORG_JURIDICA",
})


# ============================================================
# PREDICTOR
# ============================================================

class NERPredictor:
    """Carrega o modelo NER e classifica textos/documentos."""

    def __init__(
        self,
        model_name_or_path: str | Path = MODEL_DIR,
        device: str = "auto",
        max_length: int = MAX_LENGTH,
        stride: int = STRIDE,
        local_files_only: bool = True,
    ) -> None:
        if max_length < 8:
            raise ValueError("max_length deve ser pelo menos 8.")

        if stride < 0 or stride >= max_length - 2:
            raise ValueError(
                "stride deve ser >= 0 e menor que max_length - 2."
            )

        self.model_name_or_path = str(model_name_or_path)
        self.max_length = max_length
        self.stride = stride
        self.device = self._resolve_device(device)

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name_or_path,
            use_fast=True,
            local_files_only=local_files_only,
        )

        if not self.tokenizer.is_fast:
            raise RuntimeError(
                "É necessário tokenizer Fast para recuperar offsets."
            )

        self.model = AutoModelForTokenClassification.from_pretrained(
            self.model_name_or_path,
            local_files_only=local_files_only,
            low_cpu_mem_usage=False,
        )

        self.model.to(self.device)
        self.model.eval()

        self.id2label = {
            int(label_id): label
            for label_id, label in self.model.config.id2label.items()
        }

        model_types = {
            label.split("-", 1)[1]
            for label in self.id2label.values()
            if label.startswith(("B-", "I-"))
        }

        expected_types = PII_ENTITY_TYPES | NON_PII_ENTITY_TYPES
        missing = expected_types - model_types

        if missing:
            raise ValueError(
                "O modelo não contém todas as classes esperadas: "
                f"{sorted(missing)}"
            )

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        if device == "auto":
            return torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )

        selected = torch.device(device)

        if selected.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA foi solicitada, mas não está disponível."
            )

        return selected

    @staticmethod
    def _normalize_token_windows(value: Any) -> list[list[Any]]:
        if value is None or len(value) == 0:
            return []

        if isinstance(value[0], (int, float)):
            return [list(value)]

        return [list(window) for window in value]

    @staticmethod
    def _normalize_offset_windows(value: Any) -> list[list[Any]]:
        if value is None or len(value) == 0:
            return []

        first = value[0]

        # Um texto em uma única janela: [(start, end), ...]
        if (
            isinstance(first, (tuple, list))
            and len(first) == 2
            and all(isinstance(part, (int, float)) for part in first)
        ):
            return [list(value)]

        # Texto dividido em múltiplas janelas.
        return [list(window) for window in value]

    def _decode_window(
        self,
        text: str,
        offsets: list,
        predicted_ids: list[int],
        token_scores: list[float],
        window_index: int,
    ) -> list[dict]:
        entities = []
        active = None

        def close_entity():
            nonlocal active

            if active is None:
                return

            start = active["start_char"]
            end = active["end_char"]
            value = text[start:end]

            if value.strip():
                scores = active["scores"]
                entities.append({
                    "entity_type": active["entity_type"],
                    "entity_text": value,
                    "start_char": start,
                    "end_char": end,
                    "confidence": float(sum(scores) / len(scores)),
                    "window": window_index,
                })

            active = None

        for offset, label_id, score in zip(
            offsets, predicted_ids, token_scores
        ):
            start, end = int(offset[0]), int(offset[1])

            if start == end:
                continue

            label = self.id2label.get(int(label_id), "O")

            if label == "O":
                close_entity()
                continue

            prefix, separator, entity_type = label.partition("-")

            if not separator or prefix not in {"B", "I"}:
                close_entity()
                continue

            if prefix == "B":
                close_entity()
                active = {
                    "entity_type": entity_type,
                    "start_char": start,
                    "end_char": end,
                    "scores": [float(score)],
                }
                continue

            if active is not None and active["entity_type"] == entity_type:
                active["end_char"] = max(active["end_char"], end)
                active["scores"].append(float(score))
            else:
                close_entity()
                active = {
                    "entity_type": entity_type,
                    "start_char": start,
                    "end_char": end,
                    "scores": [float(score)],
                }

        close_entity()
        return entities

    def predict_entities(self, text: str) -> tuple[list[dict], int]:
        """Retorna entidades detectadas e número de janelas processadas."""
        if not isinstance(text, str):
            raise TypeError("text deve ser uma string.")

        if not text.strip():
            return [], 0

        encoded = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            stride=self.stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding=False,
        )

        input_windows = self._normalize_token_windows(
            encoded["input_ids"]
        )
        attention_windows = self._normalize_token_windows(
            encoded["attention_mask"]
        )
        offset_windows = self._normalize_offset_windows(
            encoded["offset_mapping"]
        )

        token_type_windows = None
        if "token_type_ids" in encoded:
            token_type_windows = self._normalize_token_windows(
                encoded["token_type_ids"]
            )

        if not (
            len(input_windows)
            == len(attention_windows)
            == len(offset_windows)
        ):
            raise RuntimeError(
                "Número inconsistente de janelas retornadas pelo tokenizer."
            )

        candidates = []

        for window_index, input_ids in enumerate(input_windows):
            model_inputs = {
                "input_ids": torch.tensor(
                    [input_ids],
                    dtype=torch.long,
                    device=self.device,
                ),
                "attention_mask": torch.tensor(
                    [attention_windows[window_index]],
                    dtype=torch.long,
                    device=self.device,
                ),
            }

            if token_type_windows is not None:
                model_inputs["token_type_ids"] = torch.tensor(
                    [token_type_windows[window_index]],
                    dtype=torch.long,
                    device=self.device,
                )

            with torch.inference_mode():
                logits = self.model(**model_inputs).logits[0]
                probabilities = torch.softmax(logits, dim=-1)
                scores, predicted_ids = probabilities.max(dim=-1)

            candidates.extend(
                self._decode_window(
                    text=text,
                    offsets=offset_windows[window_index],
                    predicted_ids=predicted_ids.cpu().tolist(),
                    token_scores=scores.cpu().tolist(),
                    window_index=window_index,
                )
            )

        # Remove previsões exatamente repetidas nas regiões de overlap.
        unique = {}

        for entity in candidates:
            key = (
                entity["start_char"],
                entity["end_char"],
                entity["entity_type"],
            )
            previous = unique.get(key)

            if (
                previous is None
                or entity["confidence"] > previous["confidence"]
            ):
                unique[key] = entity

        ordered = sorted(
            unique.values(),
            key=lambda item: (
                item["start_char"],
                item["end_char"],
            ),
        )

        return ordered, len(input_windows)

    def predict_document(self, text: str) -> dict:
        """
        Classificação binária derivada das entidades NER previstas.

        Uma ou mais entidades das 11 classes PII:
            COM DADO PESSOAL

        Nenhuma entidade dessas classes:
            SEM DADO PESSOAL IDENTIFICADO

        ORG_JURIDICA e DOC_EMPRESA isoladas não acionam a classe positiva.
        """
        entities, windows = self.predict_entities(text)

        personal_entities = [
            entity for entity in entities
            if entity["entity_type"] in PII_ENTITY_TYPES
        ]

        non_pii_entities = [
            entity for entity in entities
            if entity["entity_type"] in NON_PII_ENTITY_TYPES
        ]

        has_personal_data = bool(personal_entities)

        return {
            "classification": (
                CLASS_WITH_PII
                if has_personal_data
                else CLASS_WITHOUT_DETECTED_PII
            ),
            "contains_personal_data": has_personal_data,
            "personal_entity_count": len(personal_entities),
            "entities": entities,
            "personal_entities": personal_entities,
            "non_pii_entities": non_pii_entities,
            "windows": windows,
        }

    def get_info(self) -> dict:
        return {
            "model": self.model_name_or_path,
            "device": str(self.device),
            "max_length": self.max_length,
            "stride": self.stride,
            "num_labels": len(self.id2label),
        }


# ============================================================
# EXECUÇÃO REAL NA PLANILHA DE 99 REGISTROS
# ============================================================

def read_input_xlsx(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {path}")

    workbook = load_workbook(
        path,
        read_only=True,
        data_only=True,
    )

    try:
        sheet = workbook[workbook.sheetnames[0]]
        iterator = sheet.iter_rows(values_only=True)
        headers = next(iterator, None)

        if not headers:
            raise ValueError("Planilha vazia.")

        headers = [
            str(value).strip() if value is not None else ""
            for value in headers
        ]

        if "ID" not in headers or "Texto Mascarado" not in headers:
            raise ValueError(
                "A planilha precisa conter as colunas "
                "'ID' e 'Texto Mascarado'."
            )

        id_index = headers.index("ID")
        text_index = headers.index("Texto Mascarado")

        records = []

        for row_number, row in enumerate(iterator, start=2):
            raw_id = row[id_index] if id_index < len(row) else None
            raw_text = row[text_index] if text_index < len(row) else None

            if raw_text is None or not str(raw_text).strip():
                continue

            request_id = (
                str(raw_id).strip()
                if raw_id is not None
                else str(row_number)
            )

            if request_id.endswith(".0"):
                request_id = request_id[:-2]

            records.append({
                "id": request_id,
                "text": str(raw_text),
            })

        return records

    finally:
        workbook.close()


def save_results(rows: list[dict], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = output_dir / "amostra_esic_99_classificacao.xlsx"
    csv_path = output_dir / "amostra_esic_99_classificacao.csv"

    # Excel com exatamente duas colunas.
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Classificacao"
    sheet.append(["ID", "Classificação"])

    for row in rows:
        sheet.append([row["ID"], row["Classificação"]])

    header_fill = PatternFill("solid", fgColor="244062")

    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    sheet.column_dimensions["A"].width = 16
    sheet.column_dimensions["B"].width = 38
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    if rows:
        table = Table(
            displayName="ClassificacaoPII",
            ref=f"A1:B{len(rows) + 1}",
        )
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showRowStripes=True,
        )
        sheet.add_table(table)

    workbook.save(xlsx_path)

    # CSV com a mesma estrutura de duas colunas.
    with csv_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["ID", "Classificação"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return xlsx_path, csv_path


def main() -> None:
    print("\nBR-ACCESS-NER — CLASSIFICAÇÃO DE DADOS PESSOAIS")
    print("=" * 68)

    records = read_input_xlsx(INPUT_FILE)

    print(f"Planilha: {INPUT_FILE.name}")
    print(f"Registros carregados: {len(records)}")

    print("\nCarregando modelo...")

    predictor = NERPredictor(
        model_name_or_path=MODEL_DIR,
        device="auto",
        max_length=MAX_LENGTH,
        stride=STRIDE,
        local_files_only=True,
    )

    info = predictor.get_info()

    print(f"Modelo: {info['model']}")
    print(f"Dispositivo: {info['device']}")

    if info["device"].startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()

    class_counts = Counter()
    entity_counts = Counter()
    output_rows = []
    total_windows = 0
    started = time.perf_counter()

    print("\nClassificando os documentos...")

    for index, record in enumerate(records, start=1):
        result = predictor.predict_document(record["text"])

        classification = result["classification"]
        class_counts[classification] += 1
        total_windows += result["windows"]

        for entity in result["personal_entities"]:
            entity_counts[entity["entity_type"]] += 1

        output_rows.append({
            "ID": record["id"],
            "Classificação": classification,
        })

        if index % 10 == 0 or index == len(records):
            print(
                f"Processados: {index}/{len(records)}",
                flush=True,
            )

    if info["device"].startswith("cuda"):
        torch.cuda.synchronize()
        peak_vram_gb = (
            torch.cuda.max_memory_allocated() / 1024**3
        )
    else:
        peak_vram_gb = None

    elapsed = time.perf_counter() - started

    xlsx_path, csv_path = save_results(
        output_rows,
        OUTPUT_DIR,
    )

    metadata = {
        "input_file": INPUT_FILE.name,
        "model": str(MODEL_DIR),
        "device": info["device"],
        "documents_processed": len(records),
        "windows_processed": total_windows,
        "classification_counts": dict(class_counts),
        "personal_entities_by_type": dict(entity_counts),
        "runtime_seconds": round(elapsed, 3),
        "documents_per_second": (
            round(len(records) / elapsed, 3)
            if elapsed else None
        ),
        "peak_vram_gb": (
            round(peak_vram_gb, 3)
            if peak_vram_gb is not None else None
        ),
        "rule": (
            "COM DADO PESSOAL se uma ou mais entidades das 11 classes "
            "PII forem previstas. DOC_EMPRESA e ORG_JURIDICA isoladas "
            "não contam como PII."
        ),
        "limitation": (
            "A planilha não contém rótulos humanos. Este resultado "
            "é uma classificação automática exploratória; não permite "
            "calcular precisão, recall ou F1 e não comprova ausência "
            "real de dados pessoais."
        ),
    }

    metadata_path = (
        OUTPUT_DIR / "amostra_esic_99_classificacao_metadata.json"
    )

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=4,
        )

    print("\nRESULTADO DA CLASSIFICAÇÃO")
    print("=" * 68)
    print(f"Documentos processados: {len(records)}")
    print(
        f"{CLASS_WITH_PII}: "
        f"{class_counts[CLASS_WITH_PII]}"
    )
    print(
        f"{CLASS_WITHOUT_DETECTED_PII}: "
        f"{class_counts[CLASS_WITHOUT_DETECTED_PII]}"
    )
    print(f"Janelas processadas: {total_windows}")
    print(f"Tempo: {elapsed:.2f} segundos")

    if peak_vram_gb is not None:
        print(f"Pico de VRAM: {peak_vram_gb:.2f} GB")

    print("\nARQUIVOS GERADOS")
    print(f"Excel: {xlsx_path}")
    print(f"CSV: {csv_path}")
    print(f"Metadados: {metadata_path}")

    print(
        "\nATENÇÃO: 'SEM DADO PESSOAL IDENTIFICADO' significa "
        "que o modelo não detectou uma entidade das classes PII. "
        "Não é garantia de ausência de dado pessoal."
    )


if __name__ == "__main__":
    main()
