"""Sample valid records from each SoilGrids depth file without altering sources."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
SOURCE_DIR = ROOT / "DataSets" / "Soil Grid"
OUTPUT = MODULE / "data" / "processed" / "soil_sample.csv"
SUMMARY = MODULE / "evaluation" / "preprocessing_summary.json"
FEATURES = [
    "depth_top_cm", "depth_bottom_cm", "ph_h2o", "organic_carbon_g_kg",
    "total_nitrogen_g_kg", "sand_pct", "silt_pct", "clay_pct",
    "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct",
]
LOCATION = ["latitude", "longitude"]

def prepare(rows_per_depth=5000, random_state=42):
    # A balanced random sample from every layer prevents the largest file dominating.
    files = sorted(SOURCE_DIR.glob("soilgrids_*.csv"))
    if not files:
        raise FileNotFoundError(f"No SoilGrids CSV files found in {SOURCE_DIR}")
    pieces = []
    counts = {}
    required = LOCATION + FEATURES
    for path in files:
        frame = pd.read_csv(path)
        source_rows = len(frame)
        missing = sorted(set(required) - set(frame.columns))
        if missing:
            raise ValueError(f"{path.name} is missing columns: {missing}")
        for column in FEATURES + LOCATION:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        # Drop null and infinite measurements, but do not delete or rewrite raw rows.
        frame = frame.dropna(subset=required)
        finite = np.isfinite(frame[required].to_numpy(dtype=float)).all(axis=1)
        frame = frame.loc[finite]
        valid_rows = len(frame)
        take = min(rows_per_depth, valid_rows)
        if take == 0:
            raise ValueError(f"No valid soil rows remain in {path.name}")
        sample = frame.sample(n=take, random_state=random_state).copy()
        sample["source_depth_file"] = path.name
        pieces.append(sample)
        counts[path.name] = {
            "source_rows": int(source_rows),
            "valid_rows": int(valid_rows),
            "sampled_rows": int(take),
        }

    data = pd.concat(pieces, ignore_index=True)
    data = data.drop_duplicates(subset=LOCATION + ["depth_top_cm", "depth_bottom_cm"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT, index=False)
    summary = {
        "source_directory": str(SOURCE_DIR.relative_to(ROOT)),
        "sample_rows": int(len(data)),
        "rows_by_depth_file": counts,
        "sampling": "random sample per depth file",
        "random_state": random_state,
        "features": FEATURES,
        "location_columns_used_for_holdout_only": LOCATION,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Soil preprocessing: sampled {len(data)} valid rows across {len(files)} depth files.")
    return data

if __name__ == "__main__":
    prepare()
