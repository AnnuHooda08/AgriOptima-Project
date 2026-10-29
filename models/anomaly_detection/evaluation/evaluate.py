"""Score spatially held-out soil rows without claiming unobserved anomaly labels."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
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

def evaluate():
    # Hold out entire coordinate locations to test whether unusual rows generalize spatially.
    data = pd.read_csv(MODULE / "data" / "processed" / "soil_sample.csv")
    groups = data["latitude"].round(5).astype(str) + "|" + data["longitude"].round(5).astype(str)
    train_idx, test_idx = next(GroupShuffleSplit(
        n_splits=1, test_size=0.2, random_state=42
    ).split(data, groups=groups))
    train, test = data.iloc[train_idx], data.iloc[test_idx]
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("detector", IsolationForest(
            contamination=0.02, n_estimators=200, random_state=42, n_jobs=1
        )),
    ]).fit(train[FEATURES])
    scores = model.decision_function(test[FEATURES])
    flagged = model.predict(test[FEATURES]) == -1
    result = {
        "split": "coordinate-group holdout; random_state=42",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "flagged_rows": int(flagged.sum()),
        "flagged_fraction": float(flagged.mean()),
        "score_min": float(np.min(scores)),
        "score_median": float(np.median(scores)),
        "score_max": float(np.max(scores)),
        "supervised_metrics": None,
        "interpretation": "No labeled anomaly truth exists; flagged rows require review.",
    }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate()
