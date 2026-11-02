
import os

# Evita o problema de carregamento paralelo identificado no Windows.
os.environ["HF_DEACTIVATE_ASYNC_LOAD"] = "1"
os.environ["DISABLE_SAFETENSORS_CONVERSION"] = "1"

import json
import random
import shutil
from pathlib import Path

import numpy as np
import torch

from seqeval.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)

from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
    set_seed,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    ROOT / "data/processed/ner/bertimbau_esic/splits"
)

MODEL_NAME = "neuralmind/bert-base-portuguese-cased"

REPORTS_DIR = ROOT / "reports/metrics"

SEED = 42

LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
NUM_EPOCHS = 3

TRAIN_BATCH_SIZE = 1
EVAL_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 8

WARMUP_RATIO = 0.10
MAX_GRAD_NORM = 1.0

# Primeiro executamos um teste curto de integração.
# Depois definiremos NER_SMOKE_TEST=0 para o treinamento completo.
SMOKE_TEST = (
    os.getenv("NER_SMOKE_TEST", "1").lower()
    not in ("0", "false", "no")
)

SMOKE_MAX_STEPS = 8

RUN_NAME = (
    "bertimbau_esic_smoke"
    if SMOKE_TEST
    else "bertimbau_esic_full"
)

OUTPUT_DIR = ROOT / "models/training_runs" / RUN_NAME

FINAL_MODEL_DIR = (
    ROOT / "models" /
    (
        "bertimbau_esic_ner_smoke"
        if SMOKE_TEST
        else "bertimbau_esic_ner"
    )
)

METRICS_FILE = REPORTS_DIR / f"{RUN_NAME}.json"


# ============================================================
# DATASET
# ============================================================

class JsonlNERDataset(torch.utils.data.Dataset):

    FIELDS = (
        "input_ids",
        "attention_mask",
        "token_type_ids",
        "labels",
    )

    def __init__(self, path):
        self.records = []

        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                record = json.loads(line)

                for field in (
                    "input_ids",
                    "attention_mask",
                    "labels",
                ):
                    if field not in record:
                        raise ValueError(
                            f"{path.name}, linha {line_number}: "
                            f"campo ausente: {field}"
                        )

                lengths = [
                    len(record[field])
                    for field in (
                        "input_ids",
                        "attention_mask",
                        "labels",
                    )
                ]

                if len(set(lengths)) != 1:
                    raise ValueError(
                        f"Sequências inconsistentes na linha "
                        f"{line_number}: {lengths}"
                    )

                self.records.append(record)

        if not self.records:
            raise ValueError(f"Dataset vazio: {path}")

        print(
            f"Carregado {path.name}: "
            f"{len(self.records)} documentos"
        )

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = self.records[index]

        return {
            field: record[field]
            for field in self.FIELDS
            if field in record
        }


# ============================================================
# MÉTRICAS NER
# ============================================================

def build_compute_metrics(id2label, entity_types):

    def compute_metrics(eval_prediction):

        predictions = eval_prediction.predictions
        labels = eval_prediction.label_ids

        if isinstance(predictions, tuple):
            predictions = predictions[0]

        predicted_ids = np.argmax(predictions, axis=-1)

        true_predictions = []
        true_labels = []

        for prediction, label_sequence in zip(
            predicted_ids, labels
        ):
            current_predictions = []
            current_labels = []

            for predicted_id, true_id in zip(
                prediction, label_sequence
            ):
                # Ignora tokens especiais e padding.
                if int(true_id) == -100:
                    continue

                current_predictions.append(
                    id2label[int(predicted_id)]
                )

                current_labels.append(
                    id2label[int(true_id)]
                )

            true_predictions.append(current_predictions)
            true_labels.append(current_labels)

        metrics = {
            "precision": precision_score(
                true_labels, true_predictions
            ),
            "recall": recall_score(
                true_labels, true_predictions
            ),
            "f1": f1_score(
                true_labels, true_predictions
            ),
            "accuracy": accuracy_score(
                true_labels, true_predictions
            ),
        }

        report = classification_report(
            true_labels,
            true_predictions,
            output_dict=True,
            zero_division=0,
        )

        # F1 individual de cada uma das 13 categorias.
        for entity_type in entity_types:
            scores = report.get(entity_type, {})

            metrics[f"f1_{entity_type}"] = float(
                scores.get("f1-score", 0.0)
            )

        return {
            key: float(value)
            for key, value in metrics.items()
        }

    return compute_metrics


# ============================================================
# PERSISTÊNCIA
# ============================================================

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
            default=str,
        )


# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    print("\nFINE-TUNING DO BERTIMBAU")
    print("=" * 65)

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA não está disponível.")

    device_name = torch.cuda.get_device_name(0)

    print(f"GPU: {device_name}")
    print(f"PyTorch: {torch.__version__}")
    print(f"Transformers: {__import__('transformers').__version__}")
    print(f"Modo: {'SMOKE TEST' if SMOKE_TEST else 'TREINAMENTO COMPLETO'}")

    set_seed(SEED)

    # --------------------------------------------------------
    # 1. Dados
    # --------------------------------------------------------

    train_dataset = JsonlNERDataset(
        DATA_DIR / "train.jsonl"
    )

    validation_dataset = JsonlNERDataset(
        DATA_DIR / "validation.jsonl"
    )

    # --------------------------------------------------------
    # 2. Rótulos
    # --------------------------------------------------------

    label_map_path = DATA_DIR / "label_map.json"

    with label_map_path.open(
        "r", encoding="utf-8"
    ) as file:
        label_map = json.load(file)

    label2id = label_map["label2id"]

    id2label = {
        int(key): value
        for key, value in label_map["id2label"].items()
    }

    entity_types = label_map["entity_types"]

    if len(label2id) != 27:
        raise ValueError("Esperados exatamente 27 rótulos.")

    for dataset in (train_dataset, validation_dataset):
        for record in dataset.records:
            invalid = set(record["labels"]) - (
                set(range(len(label2id))) | {-100}
            )

            if invalid:
                raise ValueError(
                    f"IDs de rótulo inválidos: {invalid}"
                )

    # Verifica que os documentos não foram compartilhados.
    train_ids = {
        record["id"] for record in train_dataset.records
    }

    validation_ids = {
        record["id"] for record in validation_dataset.records
    }

    if train_ids.intersection(validation_ids):
        raise ValueError(
            "Existem documentos compartilhados entre treino e validação."
        )

    # --------------------------------------------------------
    # 3. Tokenizer e modelo
    # --------------------------------------------------------

    print("\nCarregando tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
        local_files_only=True,
    )

    data_collator = DataCollatorForTokenClassification(
        tokenizer=tokenizer,
        padding=True,
        label_pad_token_id=-100,
    )

    print("\nCarregando BERTimbau...")

    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
        local_files_only=True,
        low_cpu_mem_usage=False,
    )

    # --------------------------------------------------------
    # 4. Argumentos de treinamento
    # --------------------------------------------------------

    if SMOKE_TEST:
        eval_strategy = "steps"
        save_strategy = "steps"
        eval_steps = SMOKE_MAX_STEPS
        save_steps = SMOKE_MAX_STEPS
        max_steps = SMOKE_MAX_STEPS
        logging_steps = 2

    else:
        eval_strategy = "epoch"
        save_strategy = "epoch"
        eval_steps = None
        save_steps = None
        max_steps = -1
        logging_steps = 50

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),

        num_train_epochs=NUM_EPOCHS,
        max_steps=max_steps,

        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=EVAL_BATCH_SIZE,

        gradient_accumulation_steps=(
            GRADIENT_ACCUMULATION_STEPS
        ),

        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        lr_scheduler_type="linear",
        warmup_steps=WARMUP_RATIO,
        max_grad_norm=MAX_GRAD_NORM,

        fp16=False,
        bf16=False,
        gradient_checkpointing=False,
        torch_compile=False,

        eval_strategy=eval_strategy,
        eval_steps=eval_steps,

        save_strategy=save_strategy,
        save_steps=save_steps,
        save_total_limit=1,
        save_only_model=True,

        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,

        logging_strategy="steps",
        logging_steps=logging_steps,
        logging_first_step=True,

        eval_accumulation_steps=1,

        dataloader_num_workers=0,
        dataloader_pin_memory=False,

        remove_unused_columns=False,
        report_to="none",

        seed=SEED,
        data_seed=SEED,

        disable_tqdm=False,
    )

    # AdamW não-fused, igual ao otimizador validado
    # anteriormente na GTX 1060.
    optimizer_kwargs = {
        "lr": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "foreach": False,
    }

    # --------------------------------------------------------
    # 5. Trainer
    # --------------------------------------------------------

    trainer = Trainer(
        model=model,
        args=training_args,

        train_dataset=train_dataset,
        eval_dataset=validation_dataset,

        processing_class=tokenizer,
        data_collator=data_collator,

        compute_metrics=build_compute_metrics(
            id2label,
            entity_types,
        ),

        optimizer_cls_and_kwargs=(
            torch.optim.AdamW,
            optimizer_kwargs,
        ),
    )

    print("\nCONFIGURAÇÃO")
    print("-" * 65)
    print(f"Documentos de treino: {len(train_dataset)}")
    print(f"Documentos de validação: {len(validation_dataset)}")
    print(f"Batch size: {TRAIN_BATCH_SIZE}")
    print(f"Acumulação: {GRADIENT_ACCUMULATION_STEPS}")
    print(f"Épocas planejadas: {NUM_EPOCHS}")
    print(f"Learning rate: {LEARNING_RATE}")
    print(f"Warmup: {WARMUP_RATIO:.0%}")
    print(f"Critério do melhor modelo: F1")
    print(f"Saída: {OUTPUT_DIR}")

    # --------------------------------------------------------
    # 6. Treinamento
    # --------------------------------------------------------

    print("\nINICIANDO TREINAMENTO...")
    print("=" * 65)

    train_result = trainer.train()

    # Trainer recupera o melhor checkpoint conforme o F1.
    print("\nTREINAMENTO CONCLUÍDO.")

    print("\nAVALIAÇÃO FINAL NA VALIDAÇÃO...")

    validation_metrics = trainer.evaluate()

    # --------------------------------------------------------
    # 7. Salvar modelo e tokenizer
    # --------------------------------------------------------

    FINAL_MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    trainer.save_model(str(FINAL_MODEL_DIR))
    tokenizer.save_pretrained(str(FINAL_MODEL_DIR))

    shutil.copy2(
        label_map_path,
        FINAL_MODEL_DIR / "label_map.json",
    )

    # --------------------------------------------------------
    # 8. Relatórios
    # --------------------------------------------------------

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = {
        "model": MODEL_NAME,
        "mode": RUN_NAME,
        "seed": SEED,
        "epochs_planned": NUM_EPOCHS,
        "train_documents": len(train_dataset),
        "validation_documents": len(validation_dataset),
        "learning_rate": LEARNING_RATE,
        "train_batch_size": TRAIN_BATCH_SIZE,
        "gradient_accumulation_steps": (
            GRADIENT_ACCUMULATION_STEPS
        ),
        "validation_metrics": validation_metrics,
        "train_metrics": train_result.metrics,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "best_metric": trainer.state.best_metric,
        "log_history": trainer.state.log_history,
        "final_model_directory": str(FINAL_MODEL_DIR),
    }

    save_json(METRICS_FILE, results)

    print("\nRESULTADO FINAL")
    print("=" * 65)

    for key, value in validation_metrics.items():
        print(f"{key}: {value}")

    print(f"\nMelhor F1: {trainer.state.best_metric}")
    print(f"Melhor checkpoint: {trainer.state.best_model_checkpoint}")
    print(f"Modelo salvo em: {FINAL_MODEL_DIR}")
    print(f"Métricas salvas em: {METRICS_FILE}")

    print("\nEXECUÇÃO CONCLUÍDA!")


if __name__ == "__main__":
    main()
