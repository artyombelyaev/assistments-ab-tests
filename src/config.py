# Пути и общие константы.

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Датасет лежит в data/ или в папке из ASSISTMENTS_DATA_DIR.
DATA_DIR = Path(os.environ.get("ASSISTMENTS_DATA_DIR", ROOT / "data"))
CSV_PATH = DATA_DIR / "ThisOne.csv"
XLSX_PATH = DATA_DIR / "ThisOne.xlsx"
SQL_DIR = ROOT / "sql"

SEED = 42
ALPHA = 0.05
