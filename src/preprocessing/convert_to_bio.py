
from pathlib import Path
from collections import Counter
import json

from transformers import AutoTokenizer

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = ROOT / "data" / "interim" / "esic_ner_flat"

OUTPUT_DIR = ROOT / "data" / "processed" / "ner" / "bertimbau_esic"

MODEL_NAME = "neuralmind/bert-base-portuguese-cased"

MAX_LENGTH = 512
STRIDE = 64

SPLITS = ["train", "test"]


# =========================================================
# DESCOBRIR AS CLASSES DO TREINAMENTO
# =========================================================

def load_entity_types():

    source = SOURCE_DIR / "train_spans.jsonl"

    entity_types = set()

    with source.open("r", encoding="utf-8") as file:

        for line in file:

            if not line.strip():
                continue

            item = json.loads(line)

            for entity in item["entities"]:
                entity_types.add(entity["label"])

    return sorted(entity_types)


# =========================================================
# CONFIGURAR LABELS BIO
# =========================================================

def build_label_map(entity_types):

    labels = ["O"]

    for entity_type in entity_types:
        labels.append(f"B-{entity_type}")
        labels.append(f"I-{entity_type}")

    label2id = {
        label: index
        for index, label in enumerate(labels)
    }

    id2label = {
        str(index): label
        for label, index in label2id.items()
    }

    return label2id, id2label


# =========================================================
# NORMALIZAR SAÍDA DO TOKENIZER
# =========================================================

def as_chunks(values, field):

    if not values:
        return []

    if field == "offset_mapping":

        first = values[0]

        if (
            isinstance(first, (list, tuple))
            and len(first) == 2
            and isinstance(first[0], int)
        ):
            return [values]

    elif isinstance(values[0], int):

        return [values]

    return values


# =========================================================
# VALIDAR SPANS ORIGINAIS
# =========================================================

def validate_spans(text, entities, entity_types):

    spans = []

    for entity in entities:

        start = int(entity["start"])
        end = int(entity["end"])
        label = entity["label"]

        if label not in entity_types:
            raise ValueError(f"Classe desconhecida: {label}")

        if not (0 <= start < end <= len(text)):
            raise ValueError(
                f"Offset inválido: {start}-{end}"
            )

        spans.append((start, end, label))

    spans.sort()

    for previous, current in zip(spans, spans[1:]):

        if previous[1] > current[0]:
            raise ValueError(
                f"Sobreposição residual: {previous} / {current}"
            )

    return spans


# =========================================================
# CONVERTER UM DOCUMENTO
# =========================================================

def encode_document(
    item,
    tokenizer,
    label2id,
    entity_types
):

    text = item["text"]

    if not isinstance(text, str):
        raise ValueError("Texto inválido.")

    spans = validate_spans(
        text,
        item["entities"],
        entity_types
    )

    encoded = tokenizer(
        text,
        add_special_tokens=True,
        max_length=MAX_LENGTH,
        truncation=True,
        stride=STRIDE,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        return_attention_mask=True
    )

    input_chunks = as_chunks(
        encoded["input_ids"],
        "input_ids"
    )

    offset_chunks = as_chunks(
        encoded["offset_mapping"],
        "offset_mapping"
    )

    attention_chunks = as_chunks(
        encoded["attention_mask"],
        "attention_mask"
    )

    type_chunks = None

    if "token_type_ids" in encoded:
        type_chunks = as_chunks(
            encoded["token_type_ids"],
            "token_type_ids"
        )

    if not (
        len(input_chunks)
        == len(offset_chunks)
        == len(attention_chunks)
    ):
        raise ValueError("Quantidade de chunks inconsistente.")

    chunk_records = []

    complete_spans = set()

    for chunk_index, input_ids in enumerate(input_chunks):

        offsets = offset_chunks[chunk_index]

        labels = []
        seen_spans = set()

        overlap_ranges = {}

        for token_start, token_end in offsets:

            token_start = int(token_start)
            token_end = int(token_end)

            # Tokens especiais: [CLS], [SEP] etc.
            if token_start == token_end:
                labels.append(-100)
                continue

            if not (
                0 <= token_start < token_end <= len(text)
            ):
                raise ValueError(
                    f"Offset de token inválido: "
                    f"{token_start}-{token_end}"
                )

            # Encontrar entidades que cruzam o token.
            matches = []

            for span_index, (start, end, label) in enumerate(spans):

                if (
                    token_start < end
                    and token_end > start
                ):
                    matches.append(span_index)

            if len(matches) > 1:
                raise ValueError(
                    "Um token cruza mais de uma entidade."
                )

            # Token fora de qualquer entidade.
            if not matches:
                labels.append(label2id["O"])
                continue

            span_index = matches[0]

            start, end, label = spans[span_index]

            # Não permitir tokens parcialmente dentro
            # de uma entidade.
            if not (
                token_start >= start
                and token_end <= end
            ):
                raise ValueError(
                    f"Token cruza limite da entidade: "
                    f"{token_start}-{token_end} / {start}-{end}"
                )

            # Primeiro token da entidade no chunk.
            if span_index not in seen_spans:

                bio_label = f"B-{label}"
                seen_spans.add(span_index)

            else:

                bio_label = f"I-{label}"

            labels.append(label2id[bio_label])

            overlap_ranges.setdefault(
                span_index, []
            ).append((token_start, token_end))

        # Verificar cobertura integral das entidades.
        for span_index, ranges in overlap_ranges.items():

            start, end, label = spans[span_index]

            first_char = min(r[0] for r in ranges)
            last_char = max(r[1] for r in ranges)

            if first_char == start and last_char == end:
                complete_spans.add(span_index)

        tokens = tokenizer.convert_ids_to_tokens(
            input_ids
        )

        record = {
            "id": item["id"],
            "chunk_index": chunk_index,
            "input_ids": input_ids,
            "attention_mask": attention_chunks[chunk_index],
            "labels": labels,
            "tokens": tokens,
            "offset_mapping": [
                [int(start), int(end)]
                for start, end in offsets
            ],
            "gold_entities": [
                {
                    "start": spans[index][0],
                    "end": spans[index][1],
                    "label": spans[index][2]
                }
                for index in overlap_ranges
            ]
        }

        if type_chunks is not None:
            record["token_type_ids"] = type_chunks[chunk_index]

        if not (
            len(record["input_ids"])
            == len(record["labels"])
            == len(record["attention_mask"])
            == len(record["tokens"])
            == len(record["offset_mapping"])
        ):
            raise ValueError("Comprimentos de sequência inconsistentes.")

        chunk_records.append(record)

    # Toda entidade original deve estar integralmente
    # representada em pelo menos uma janela.
    if len(complete_spans) != len(spans):

        missing = len(spans) - len(complete_spans)

        raise ValueError(
            f"{missing} entidades sem cobertura integral "
            "em nenhuma janela."
        )

    return chunk_records


# =========================================================
# PROCESSAR TREINO OU TESTE
# =========================================================

def process_split(
    split,
    tokenizer,
    label2id,
    entity_types
):

    source = SOURCE_DIR / f"{split}_spans.jsonl"

    output = OUTPUT_DIR / f"{split}.jsonl"

    quarantine = OUTPUT_DIR / f"{split}_quarantine.jsonl"

    stats = Counter()
    label_counts = Counter()

    print(f"\nProcessando {split.upper()}...")

    with (
        source.open("r", encoding="utf-8") as input_file,
        output.open("w", encoding="utf-8") as output_file,
        quarantine.open("w", encoding="utf-8") as quarantine_file
    ):

        for line_number, line in enumerate(input_file, start=1):

            if not line.strip():
                continue

            item = json.loads(line)

            stats["documents"] += 1

            try:

                chunks = encode_document(
                    item,
                    tokenizer,
                    label2id,
                    entity_types
                )

                for chunk in chunks:

                    output_file.write(
                        json.dumps(
                            chunk,
                            ensure_ascii=False
                        ) + "\n"
                    )

                    stats["chunks"] += 1
                    stats["tokens"] += len(chunk["input_ids"])

                    for label_id in chunk["labels"]:

                        if label_id != -100:
                            label = list(label2id.keys())[label_id]
                            label_counts[label] += 1

                stats["valid_documents"] += 1
                stats["entities"] += len(item["entities"])

            except Exception as error:

                stats["rejected_documents"] += 1

                quarantine_file.write(
                    json.dumps({
                        "id": item.get(
                            "id",
                            f"{split}_{line_number}"
                        ),
                        "error": str(error)
                    }, ensure_ascii=False) + "\n"
                )

    print(f"Documentos: {stats['documents']:,}")
    print(f"Documentos válidos: {stats['valid_documents']:,}")
    print(f"Documentos rejeitados: {stats['rejected_documents']:,}")
    print(f"Chunks gerados: {stats['chunks']:,}")
    print(f"Tokens processados: {stats['tokens']:,}")
    print(f"Entidades originais: {stats['entities']:,}")

    print("\nDISTRIBUIÇÃO BIO:")

    for label, count in label_counts.most_common():
        print(f"{label}: {count:,}")

    return stats, label_counts


# =========================================================
# EXECUÇÃO
# =========================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # O vocabulário de classes é derivado somente
    # do conjunto de treinamento.
    entity_types = load_entity_types()

    label2id, id2label = build_label_map(
        entity_types
    )

    print("Classes encontradas:")
    print(entity_types)

    print(f"\nTotal de rótulos BIO: {len(label2id)}")

    print("\nCarregando tokenizer BERTimbau...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
        do_lower_case=False
    )

    if not tokenizer.is_fast:
        raise RuntimeError(
            "Precisamos de um tokenizer Fast para usar offsets."
        )

    print("Tokenizer carregado!")
    print(f"Modelo: {MODEL_NAME}")
    print(f"Limite: {MAX_LENGTH}")
    print(f"Stride: {STRIDE}")

    # Salvar mapeamento dos rótulos.
    with (OUTPUT_DIR / "label_map.json").open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump({
            "model_name": MODEL_NAME,
            "entity_types": entity_types,
            "label2id": label2id,
            "id2label": id2label,
            "max_length": MAX_LENGTH,
            "stride": STRIDE
        }, file, ensure_ascii=False, indent=2)

    results = {}

    for split in SPLITS:

        stats, label_counts = process_split(
            split,
            tokenizer,
            label2id,
            entity_types
        )

        results[split] = {
            "stats": dict(stats),
            "label_counts": dict(label_counts)
        }

    with (OUTPUT_DIR / "dataset_info.json").open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump({
            "model": MODEL_NAME,
            "max_length": MAX_LENGTH,
            "stride": STRIDE,
            "labels": len(label2id),
            "results": results
        }, file, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print("CONVERSÃO BIO FINALIZADA")
    print("=" * 65)

    print(f"Diretório: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
