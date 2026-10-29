"""Validate and clean loss measurements while keeping their source citations auditable."""
from pathlib import Path
import json
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_FILE = ROOT / "DataSets" / "Food Loss" / "post_harvest_loss_2022_state_stage.csv"
OUTPUT = MODULE / "data" / "processed" / "loss_records.csv"
SUMMARY = MODULE / "evaluation" / "preprocessing_summary.json"
CATEGORICAL = ["state", "crop", "loss_type", "stage"]
TARGET = "loss_percentage"

def prepare():
    # Keep the original source and citation columns untouched; model only on measured predictors.
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Loss dataset not found: {RAW_FILE}")
    source = pd.read_csv(RAW_FILE)
    source_rows = len(source)
    required = CATEGORICAL + [TARGET]
    missing = sorted(set(required) - set(source.columns))
    if missing:
        raise ValueError(f"Required loss columns are missing: {missing}")
    data = source[required].copy()
    for name in CATEGORICAL:
        data[name] = data[name].astype("string").str.strip()
    data[TARGET] = pd.to_numeric(data[TARGET], errors="coerce")

    # Remove incomplete or physically impossible target values and exact duplicate records.
    valid = data[CATEGORICAL].notna().all(axis=1)
    valid &= data[CATEGORICAL].apply(lambda col: col.str.len().fillna(0).gt(0)).all(axis=1)
    valid &= data[TARGET].between(0, 100, inclusive="both")
    clean = data.loc[valid].drop_duplicates().reset_index(drop=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT, index=False)
    summary = {
        "source_file": str(RAW_FILE.relative_to(ROOT)),
        "source_rows": int(source_rows),
        "valid_unique_rows": int(len(clean)),
        "removed_or_duplicate_rows": int(source_rows - len(clean)),
        "target_range": [float(clean[TARGET].min()), float(clean[TARGET].max())],
        "features": CATEGORICAL,
        "target": TARGET,
        "source_years": sorted(pd.read_csv(RAW_FILE, usecols=["year"])["year"].dropna().unique().astype(int).tolist()),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Loss preprocessing: {len(clean)} clean records from {source_rows}.")
    return clean

if __name__ == "__main__":
    prepare()
