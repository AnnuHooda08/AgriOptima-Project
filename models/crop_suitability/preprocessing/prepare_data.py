"""Validate and clean the preserved crop suitability table into a model-ready CSV."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_DATA = ROOT / "DataSets" / "crop_suitability.csv"
OUTPUT = MODULE / "data" / "processed" / "crop_suitability_processed.csv"
REPORT = MODULE / "evaluation" / "preprocessing_summary.json"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"

def prepare():
    # Read source data without ever writing back to the user's CSV.
    if not RAW_DATA.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_DATA}")
    data = pd.read_csv(RAW_DATA)
    original_rows = len(data)
    data.columns = [str(name).strip() for name in data.columns]
    required = FEATURES + [TARGET]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Required suitability columns are missing: {missing}")

    # Convert every measurement explicitly; malformed values become removable NaNs.
    for name in FEATURES:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    data[TARGET] = data[TARGET].astype("string").str.strip()
    finite = np.isfinite(data[FEATURES].to_numpy(dtype=float)).all(axis=1)
    valid = finite & data[TARGET].notna().to_numpy() & data[TARGET].ne("").to_numpy()
    clean = data.loc[valid, required].drop_duplicates().reset_index(drop=True)

    # Keep a small audit summary so row loss is visible and reproducible.
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT, index=False)
    summary = {
        "source_file": str(RAW_DATA.relative_to(ROOT)),
        "source_rows": int(original_rows),
        "clean_rows": int(len(clean)),
        "removed_rows": int(original_rows - len(clean)),
        "duplicate_rows_removed_after_validation": int(valid.sum() - len(clean)),
        "class_count": int(clean[TARGET].nunique()),
        "features": FEATURES,
        "target": TARGET,
    }
    REPORT.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Suitability preprocessing: {len(clean)} clean rows from {original_rows}.")
    return clean

if __name__ == "__main__":
    prepare()
