"""Small tests for the Linear Regression data and prediction workflow."""

import math

import pandas as pd
import pytest

from pathlib import Path
import sys

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "inference"))
from prepare_linear_data import MODEL_DATA, RAW_FILE, load_model_data, prepare_data  # noqa: E402
from predict_linear import predict  # noqa: E402


EXAMPLE_LAGS = {"lag_1": 2090, "lag_2": 2090, "lag_3": 1980, "lag_12": 2100}


def test_maize_source_and_preprocessing_are_available():
    """Check that source CSV loads and creates the expected time-series rows."""
    assert RAW_FILE.exists()
    data = prepare_data()
    assert MODEL_DATA.exists()
    assert len(data) == 265
    assert data["date"].is_monotonic_increasing
    assert {"price", "lag_1", "lag_2", "lag_3", "lag_12", "month", "year"}.issubset(data.columns)
    assert (data["price"] > 0).all()


def test_prepared_dataset_loads_with_calendar_features():
    data = load_model_data()
    assert isinstance(data, pd.DataFrame)
    assert data["month"].between(1, 12).all()
    assert data[["lag_1", "lag_2", "lag_3", "lag_12"]].notna().all().all()


def test_saved_linear_pipeline_returns_a_price_estimate():
    estimate = predict(EXAMPLE_LAGS, month=1, year=2024)
    assert isinstance(estimate, float)
    assert math.isfinite(estimate)
    assert estimate > 0


@pytest.mark.parametrize(
    ("lags", "month", "year"),
    [
        ({"lag_1": 100, "lag_2": 90, "lag_3": 80}, 1, 2024),
        ({"lag_1": 100, "lag_2": 90, "lag_3": 80, "lag_12": float("nan")}, 1, 2024),
        ({"lag_1": 100, "lag_2": 90, "lag_3": 80, "lag_12": 70}, 13, 2024),
        ({"lag_1": -1, "lag_2": 90, "lag_3": 80, "lag_12": 70}, 1, 2024),
    ],
)
def test_invalid_prediction_inputs_are_rejected(lags, month, year):
    with pytest.raises(ValueError):
        predict(lags, month=month, year=year)
