
from pathlib import Path
import re
import pandas as pd

# =========================================================
# CONFIGURAÇÕES
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = PROJECT_ROOT / "data" / "raw" / "falabr"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "falabr_pedidos_2015_2023.csv"

CHUNK_SIZE = 20_000
EXPECTED_YEARS = set(range(2015, 2024))

SELECTED_COLUMNS = [
    "IdPedido",
    "ProtocoloPedido",
    "Esfera",
    "OrgaoDestinatario",
    "DataRegistro",
    "OrigemSolicitacao",
    "AssuntoPedido",
    "SubAssuntoPedido",
    "Tag",
    "ResumoSolicitacao",
    "DetalhamentoSolicitacao",
]

# =========================================================
# DESCOBERTA DOS ARQUIVOS
# =========================================================

files_by_year = {}

for file in SOURCE_DIR.glob("*.csv"):
    match = re.fullmatch(
        r"\d{8}_Pedidos_csv_(\d{4})\.csv",
        file.name,
        re.IGNORECASE
    )

    if match:
        year = int(match.group(1))
        files_by_year[year] = file

if set(files_by_year) != EXPECTED_YEARS:
    raise FileNotFoundError(
        f"Anos esperados: {sorted(EXPECTED_YEARS)}. "
        f"Anos encontrados: {sorted(files_by_year)}"
    )

files = sorted(files_by_year.items())

print("=" * 65)
print("CONSOLIDAÇÃO FALABR")
print("=" * 65)

print(f"Arquivos encontrados: {len(files)}")

# =========================================================
# CONSOLIDAÇÃO
# =========================================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

total_records = 0
first_chunk = True

summary_filled = 0
detail_filled = 0
records_without_text = 0

for year, file in files:

    print(f"\nProcessando {year}: {file.name}")

    year_records = 0

    reader = pd.read_csv(
        file,
        sep=None,
        engine="python",
        encoding="utf-16",
        dtype=str,
        usecols=SELECTED_COLUMNS,
        chunksize=CHUNK_SIZE
    )

    for chunk in reader:

        summary = chunk["ResumoSolicitacao"].fillna("").str.strip()
        detail = chunk["DetalhamentoSolicitacao"].fillna("").str.strip()

        summary_filled += int(summary.ne("").sum())
        detail_filled += int(detail.ne("").sum())

        records_without_text += int(
            (summary.eq("") & detail.eq("")).sum()
        )

        chunk.insert(0, "AnoFonte", year)

        chunk.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
            mode="w" if first_chunk else "a",
            header=first_chunk
        )

        first_chunk = False

        year_records += len(chunk)
        total_records += len(chunk)

    print(f"Registros processados: {year_records:,}")

# =========================================================
# RELATÓRIO FINAL
# =========================================================

print("\n" + "=" * 65)
print("CONSOLIDAÇÃO FINALIZADA")
print("=" * 65)

print(f"Total de registros: {total_records:,}")
print(f"Resumos preenchidos: {summary_filled:,}")
print(f"Detalhamentos preenchidos: {detail_filled:,}")
print(f"Registros sem textos: {records_without_text:,}")

print(f"\nArquivo gerado: {OUTPUT_FILE}")

print(
    f"Tamanho: {OUTPUT_FILE.stat().st_size / (1024**2):.2f} MB"
)
