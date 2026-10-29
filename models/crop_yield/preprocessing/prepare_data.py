"""Clean yield records, explain exclusions, and write reusable model features."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_FILE = ROOT / "DataSets" / "Yeild" / "crop_production_haryana_punjab_1997_2019.csv"
DATA_DIR = MODULE / "data" / "processed"
REPORT_DIR = MODULE / "reports" / "current"
FEATURES = ["State", "District", "Crop", "Season", "YearStart", "Area"]
TARGET = "Yield"

def prepare():
    # Keep the original CSV read-only and validate its expected schema first.
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Yield dataset not found: {RAW_FILE}")
    original = pd.read_csv(RAW_FILE)
    source_rows = len(original)
    original.columns = [str(name).strip() for name in original.columns]
    required = ["State", "District", "Crop", "Year", "Season", "Area",
                "Area Units", "Production", "Production Units", "Yield"]
    missing = sorted(set(required) - set(original.columns))
    if missing:
        raise ValueError(f"Required yield columns are missing: {missing}")

    # Drop exact duplicates and normalize types before testing row quality.
    data = original.drop_duplicates().copy()
    duplicate_count = source_rows - len(data)
    for name in ["State", "District", "Crop", "Season", "Area Units", "Production Units"]:
        data[name] = data[name].astype("string").str.strip()
    for name in ["Area", "Production", TARGET]:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    data["YearStart"] = pd.to_numeric(
        data["Year"].astype("string").str.extract(r"((?:19|20)\d{2})", expand=False),
        errors="coerce",
    )

    # Record one or more readable reasons for every rejected row.
    reasons = pd.Series("", index=data.index, dtype="string")
    def mark(mask, reason):
        mask = mask.fillna(False)
        reasons.loc[mask] = reasons.loc[mask].apply(
            lambda old: f"{old}; {reason}" if old else reason
        )
    for column in ["State", "District", "Crop", "Season"]:
        mark(data[column].isna() | data[column].str.len().fillna(0).eq(0), f"missing_{column}")
    mark(data["YearStart"].isna(), "invalid_or_missing_year")
    mark(~np.isfinite(data["Area"]), "missing_or_invalid_area")
    mark(data["Area"].notna() & (data["Area"] <= 0), "nonpositive_area")
    mark(~np.isfinite(data[TARGET]), "missing_or_invalid_yield")
    mark(data[TARGET].notna() & (data[TARGET] <= 0), "nonpositive_yield")
    valid_area_units = data["Area Units"].str.lower().isin(["hectare", "hectares", "ha"])
    mark(~valid_area_units, "incompatible_area_units")
    valid_production_units = data["Production Units"].str.lower().isin(
        ["tonne", "tonnes", "metric tonne", "metric tonnes", "metric ton", "metric tons"]
    )
    mark(~valid_production_units, "incompatible_production_units")

    clean = data.loc[reasons.eq("")].copy()
    clean["YearStart"] = clean["YearStart"].astype(int)
    rejected = data.loc[reasons.ne("")].copy()
    rejected["exclusion_reason"] = reasons.loc[reasons.ne("")]
    model_data = clean[FEATURES + [TARGET]].drop_duplicates().reset_index(drop=True)

    # Save clean data and audits beside this model, not over the source dataset.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(DATA_DIR / "crop_yield_cleaned.csv", index=False)
    model_data.to_csv(DATA_DIR / "crop_yield_model_data.csv", index=False)
    rejected.to_csv(REPORT_DIR / "excluded_rows_audit.csv", index=False)
    summary = {
        "source_file": str(RAW_FILE.relative_to(ROOT)),
        "source_rows": int(source_rows),
        "exact_duplicates_removed": int(duplicate_count),
        "valid_clean_rows": int(len(clean)),
        "excluded_rows": int(len(rejected)),
        "model_rows": int(len(model_data)),
        "year_min": int(model_data["YearStart"].min()),
        "year_max": int(model_data["YearStart"].max()),
        "target": TARGET,
        "features": FEATURES,
    }
    (REPORT_DIR / "preprocessing_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    profile = pd.DataFrame({
        "column": FEATURES + [TARGET],
        "role": ["input"] * len(FEATURES) + ["target"],
        "data_type": [str(model_data[c].dtype) for c in FEATURES + [TARGET]],
        "unique_values": [int(model_data[c].nunique()) for c in FEATURES + [TARGET]],
    })
    profile.to_csv(REPORT_DIR / "feature_profile.csv", index=False)
    print(f"Yield preprocessing: {len(model_data)} valid rows from {source_rows}; excluded {len(rejected)}.")
    return model_data

if __name__ == "__main__":
    prepare()
