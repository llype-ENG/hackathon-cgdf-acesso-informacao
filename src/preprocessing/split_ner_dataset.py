
import csv
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = ROOT / "data" / "processed" / "ner" / "bertimbau_esic"
OUTPUT_DIR = INPUT_DIR / "splits"

TRAIN_FILE = INPUT_DIR / "train.jsonl"
TEST_FILE = INPUT_DIR / "test.jsonl"
LABEL_MAP_FILE = INPUT_DIR / "label_map.json"

SEED = 42
VALIDATION_RATIO = 0.10

ID_CANDIDATES = (
    "document_id",
    "doc_id",
    "id",
    "pedido_id",
)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido em {path}, linha {line_number}"
                ) from error

    return records


def get_document_id(record: dict):
    for key in ID_CANDIDATES:
        if key in record:
            return record[key]

    available_keys = list(record.keys())

    raise KeyError(
        "Não foi possível identificar o documento. "
        f"Campos encontrados: {available_keys}"
    )


def group_by_document(records: list[dict]) -> dict:
    groups = defaultdict(list)

    for record in records:
        document_id = get_document_id(record)
        groups[document_id].append(record)

    return groups


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def main():
    print("\nPreparando divisão do dataset NER...")

    train_records = load_jsonl(TRAIN_FILE)
    test_records = load_jsonl(TEST_FILE)

    train_groups = group_by_document(train_records)
    test_groups = group_by_document(test_records)

    train_ids = list(train_groups.keys())
    test_ids = set(test_groups.keys())

    if not train_ids:
        raise ValueError("O conjunto de treino está vazio.")

    if len(train_ids) < 2:
        raise ValueError("Documentos insuficientes para divisão.")

    overlap = set(train_ids).intersection(test_ids)

    if overlap:
        raise ValueError(
            f"Foram encontrados {len(overlap)} IDs em comum "
            "entre treino e teste. Verifique a origem dos dados."
        )

    # Embaralha documentos, não chunks individuais.
    rng = random.Random(SEED)
    shuffled_ids = train_ids.copy()
    rng.shuffle(shuffled_ids)

    validation_size = max(
        1,
        round(len(shuffled_ids) * VALIDATION_RATIO)
    )

    validation_ids = set(shuffled_ids[:validation_size])
    final_train_ids = set(shuffled_ids[validation_size:])

    # Preserva a ordem original dos registros.
    final_train = [
        record
        for record in train_records
        if get_document_id(record) in final_train_ids
    ]

    validation = [
        record
        for record in train_records
        if get_document_id(record) in validation_ids
    ]

    # Verificações antes de gravar.
    assert not final_train_ids.intersection(validation_ids)
    assert len(final_train_ids) + len(validation_ids) == len(train_ids)
    assert len(final_train) + len(validation) == len(train_records)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    write_jsonl(OUTPUT_DIR / "train.jsonl", final_train)
    write_jsonl(OUTPUT_DIR / "validation.jsonl", validation)

    # Copia o teste original sem modificá-lo.
    shutil.copyfile(
        TEST_FILE,
        OUTPUT_DIR / "test.jsonl"
    )

    if LABEL_MAP_FILE.exists():
        shutil.copyfile(
            LABEL_MAP_FILE,
            OUTPUT_DIR / "label_map.json"
        )

    # Relatório da divisão.
    summary = [
        {
            "dataset": "train",
            "documents": len(final_train_ids),
            "chunks": len(final_train),
        },
        {
            "dataset": "validation",
            "documents": len(validation_ids),
            "chunks": len(validation),
        },
        {
            "dataset": "test",
            "documents": len(test_groups),
            "chunks": len(test_records),
        },
    ]

    with (OUTPUT_DIR / "split_summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["dataset", "documents", "chunks"]
        )
        writer.writeheader()
        writer.writerows(summary)

    metadata = {
        "random_seed": SEED,
        "validation_ratio": VALIDATION_RATIO,
        "original_training_documents": len(train_ids),
        "original_test_documents": len(test_ids),
        "train_documents": len(final_train_ids),
        "validation_documents": len(validation_ids),
        "test_documents": len(test_ids),
        "train_chunks": len(final_train),
        "validation_chunks": len(validation),
        "test_chunks": len(test_records),
        "test_modified": False,
        "split_by": "document_id",
    }

    with (OUTPUT_DIR / "split_info.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(metadata, file, ensure_ascii=False, indent=4)

    print("\nDIVISÃO CONCLUÍDA")
    print("=" * 55)

    for item in summary:
        print(
            f"{item['dataset'].upper():12} "
            f"Documentos: {item['documents']:5} | "
            f"Chunks: {item['chunks']:5}"
        )

    print("=" * 55)
    print(f"Semente: {SEED}")
    print("IDs compartilhados entre conjuntos: 0")
    print("Teste original preservado: SIM")
    print(f"\nArquivos salvos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
