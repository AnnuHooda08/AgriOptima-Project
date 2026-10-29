"""Assign a complete numeric soil record to one descriptive cluster."""
from pathlib import Path
import math
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "soil_kmeans.joblib"

def predict(values):
    saved = joblib.load(ARTIFACT)
    features = saved["features"]
    missing = [name for name in features if name not in values]
    if missing:
        raise ValueError(f"Missing soil measurements: {missing}")
    row = pd.DataFrame([{name: float(values[name]) for name in features}], columns=features)
    if not all(math.isfinite(value) for value in row.iloc[0]):
        raise ValueError("Soil measurements must be finite numbers.")
    # Cluster IDs are arbitrary and do not mean a crop is suitable.
    return int(saved["model"].predict(row)[0])

if __name__ == "__main__":
    sample = dict(depth_top_cm=0, depth_bottom_cm=5, ph_h2o=7,
        organic_carbon_g_kg=10, total_nitrogen_g_kg=1, sand_pct=35,
        silt_pct=35, clay_pct=30, bulk_density_g_cm3=1.3,
        cec_cmol_kg=15, coarse_fragments_vol_pct=3)
    print("Descriptive cluster:", predict(sample))
