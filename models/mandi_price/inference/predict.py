"""Predict next month's experimental maize price from calendar-month lags."""
from pathlib import Path
import math
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "maize_price_hgb.joblib"

def predict(lags, month, year):
    saved = joblib.load(ARTIFACT)
    row = {**lags, "month": int(month), "year": int(year)}
    missing = [name for name in saved["features"] if name not in row]
    if missing:
        raise ValueError(f"Missing price features: {missing}")
    values = [float(row[name]) for name in saved["features"]]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Price features must be finite numbers.")
    if not 1 <= int(month) <= 12 or any(float(lags[name]) <= 0 for name in ["lag_1", "lag_2", "lag_3", "lag_12"]):
        raise ValueError("Month must be 1-12 and all lag prices must be positive.")
    # This model underperformed persistence in the recorded holdout; treat as experimental.
    return float(saved["model"].predict(pd.DataFrame([row], columns=saved["features"]))[0])

if __name__ == "__main__":
    sample_lags = dict(lag_1=1000, lag_2=950, lag_3=920, lag_12=800)
    print("Experimental forecast:", predict(sample_lags, month=1, year=2025))
