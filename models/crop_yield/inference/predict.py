"""Validate yield inputs and return a model estimate in tonnes per hectare."""
from pathlib import Path
import math
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "random_forest.joblib"
FEATURES = ["State", "District", "Crop", "Season", "YearStart", "Area"]

def predict(values):
    # Preserve training field names and reject missing or invalid numeric values.
    missing = [name for name in FEATURES if name not in values]
    if missing:
        raise ValueError(f"Missing yield inputs: {missing}")
    year = float(values["YearStart"])
    area = float(values["Area"])
    if not math.isfinite(year) or not math.isfinite(area) or area <= 0:
        raise ValueError("YearStart and Area must be finite; Area must be positive.")
    row = pd.DataFrame([{name: values[name] for name in FEATURES}])
    return float(joblib.load(ARTIFACT).predict(row)[0])

if __name__ == "__main__":
    sample = dict(State="Punjab", District="Ludhiana", Crop="Wheat",
                  Season="Rabi", YearStart=2024, Area=1000)
    print("Predicted yield:", predict(sample))
