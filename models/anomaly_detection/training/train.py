"""Fit a final Isolation Forest on the clean soil sample."""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODULE = Path(__file__).resolve().parents[1]
FEATURES = [
    "depth_top_cm", "depth_bottom_cm", "ph_h2o", "organic_carbon_g_kg",
    "total_nitrogen_g_kg", "sand_pct", "silt_pct", "clay_pct",
    "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct",
]

def build_model():
    # The contamination setting is a review threshold, not a known error rate.
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("detector", IsolationForest(
            contamination=0.02, n_estimators=200, random_state=42, n_jobs=1
        )),
    ])

def train():
    data = pd.read_csv(MODULE / "data" / "processed" / "soil_sample.csv")
    model = build_model().fit(data[FEATURES])
    artifact = MODULE / "artifacts" / "soil_isolation_forest.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, artifact)
    print(f"Fitted Isolation Forest on {len(data)} soil records; saved {artifact}")
    return model

if __name__ == "__main__":
    train()
