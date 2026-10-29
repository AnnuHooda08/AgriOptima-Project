"""Score a soil record and mark whether it deserves human review."""
from pathlib import Path
import math
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "soil_isolation_forest.joblib"

def predict(values):
    saved = joblib.load(ARTIFACT)
    features = saved["features"]
    missing = [name for name in features if name not in values]
    if missing:
        raise ValueError(f"Missing soil measurements: {missing}")
    row = pd.DataFrame([{name: float(values[name]) for name in features}], columns=features)
    if not all(math.isfinite(value) for value in row.iloc[0]):
        raise ValueError("Soil measurements must be finite numbers.")
    model = saved["model"]
    # A flag is a request to review the record, not proof that it is wrong.
    return {
        "score": float(model.decision_function(row)[0]),
        "review_candidate": bool(model.predict(row)[0] == -1),
    }

if __name__ == "__main__":
    sample = dict(depth_top_cm=0, depth_bottom_cm=5, ph_h2o=7,
        organic_carbon_g_kg=10, total_nitrogen_g_kg=1, sand_pct=35,
        silt_pct=35, clay_pct=30, bulk_density_g_cm3=1.3,
        cec_cmol_kg=15, coarse_fragments_vol_pct=3)
    print("Soil review result:", predict(sample))
