"""Estimate post-harvest loss percentage for a crop and stage combination."""
from pathlib import Path
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "post_harvest_loss_rf.joblib"

def predict(values):
    saved = joblib.load(ARTIFACT)
    features = saved["features"]
    missing = [name for name in features if name not in values]
    if missing:
        raise ValueError(f"Missing loss inputs: {missing}")
    # Trim text values consistently with preprocessing; unknown categories are allowed.
    row = pd.DataFrame([{name: str(values[name]).strip() for name in features}], columns=features)
    prediction = float(saved["model"].predict(row)[0])
    return min(100.0, max(0.0, prediction))

if __name__ == "__main__":
    sample = dict(state="Haryana", crop="Bajra",
                  loss_type="Farm Operations", stage="Harvesting")
    print("Experimental loss estimate (%):", predict(sample))
