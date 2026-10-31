"""Validate user inputs and run the saved one-month-ahead maize model."""

from __future__ import annotations

import math
from pathlib import Path

import joblib
import pandas as pd


MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "maize_price_linear_regression.joblib"
REQUIRED_LAGS = ("lag_1", "lag_2", "lag_3", "lag_12")


def predict(lags: dict[str, float], month: int, year: int) -> float:
    """Return an estimated monthly national maize modal price in Rs/quintal.

    Lags must be the actual observed national monthly median prices from 1, 2,
    3, and 12 calendar months before the requested target month.
    """
    if not isinstance(lags, dict):
        raise ValueError("lags must be a dictionary containing lag_1, lag_2, lag_3, and lag_12.")
    missing = [name for name in REQUIRED_LAGS if name not in lags]
    if missing:
        raise ValueError(f"Missing required price lags: {missing}")
    try:
        month_value = int(month)
        year_value = int(year)
        values = {name: float(lags[name]) for name in REQUIRED_LAGS}
    except (TypeError, ValueError) as error:
        raise ValueError("Month, year, and lag prices must be numeric values.") from error
    if month_value != month or not 1 <= month_value <= 12:
        raise ValueError("month must be a whole number from 1 to 12.")
    if year_value != year or not 2000 <= year_value <= 2200:
        raise ValueError("year must be a whole number between 2000 and 2200.")
    if any(not math.isfinite(value) or value <= 0 for value in values.values()):
        raise ValueError("All lag prices must be finite positive numbers in Rs/quintal.")
    if not ARTIFACT.exists():
        raise FileNotFoundError(f"Linear Regression artifact not found: {ARTIFACT}")

    saved = joblib.load(ARTIFACT)
    row = {**values, "month": month_value, "year": year_value}
    frame = pd.DataFrame([row], columns=saved["features"])
    estimate = float(saved["model"].predict(frame)[0])
    if not math.isfinite(estimate) or estimate <= 0:
        raise ValueError("The model produced a nonpositive or invalid estimate; do not use it as a price quote.")
    return estimate


if __name__ == "__main__":
    example_lags = {"lag_1": 2090, "lag_2": 2090, "lag_3": 1980, "lag_12": 2100}
    print(f"Estimated national maize monthly modal price: Rs {predict(example_lags, month=1, year=2024):.2f}/quintal")
