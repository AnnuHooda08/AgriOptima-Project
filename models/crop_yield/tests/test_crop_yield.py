"""Tests for the reproducible yield data and inference contract."""
from pathlib import Path
import sys
import joblib
import pandas as pd
import pytest

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "inference"))
sys.path.insert(0, str(MODULE / "preprocessing"))
from predict import predict
from prepare_data import FEATURES, TARGET, prepare


def sample():
    """Use categories known to exist in the supported training dataset."""
    return dict(State="Punjab", District="Barnala", Crop="Wheat",
                Season="Rabi", YearStart=2024, Area=1000)


def test_preprocessing_has_supported_schema_and_no_production_leakage():
    data = prepare()
    assert set(FEATURES + [TARGET]).issubset(data.columns)
    assert "Production" not in FEATURES
    assert data[TARGET].notna().all()
    assert (data["Area"] > 0).all()


def test_production_artifact_loads_and_predicts_valid_finite_yield():
    artifact = MODULE / "artifacts/random_forest.joblib"
    pipeline = joblib.load(artifact)
    assert hasattr(pipeline, "predict")
    result = predict(sample(), artifact)
    assert isinstance(result, float)
    assert result >= 0


def test_challenger_artifact_predicts_when_available():
    artifacts = list((MODULE / "artifacts").glob("challenger_*.joblib"))
    if not artifacts:
        pytest.skip("Challenger artifact is created after candidate comparison.")
    assert predict({"Crop": "Wheat", "Season": "Rabi"}, artifacts[0]) >= 0


def test_missing_inputs_are_reported():
    with pytest.raises(ValueError, match="Missing yield inputs"):
        predict({"State": "Punjab"})


@pytest.mark.parametrize("area", [0, -1, float("nan"), float("inf"), "not a number"])
def test_invalid_area_is_rejected(area):
    values = sample()
    values["Area"] = area
    with pytest.raises(ValueError, match="Area"):
        predict(values)


def test_invalid_year_is_rejected():
    values = sample()
    values["YearStart"] = 2024.5
    with pytest.raises(ValueError, match="YearStart"):
        predict(values)


@pytest.mark.parametrize(("key", "value"), [
    ("State", "Atlantis"), ("District", "Unknown District"),
    ("Crop", "Unknown Crop"), ("Season", "Rainy-Unknown"),
])
def test_unknown_categories_are_reported(key, value):
    values = sample()
    values[key] = value
    with pytest.raises(ValueError, match=f"Unknown {key}"):
        predict(values)


def test_artifact_input_features_match_documented_fields():
    model = joblib.load(MODULE / "artifacts/random_forest.joblib")
    assert list(model.feature_names_in_) == FEATURES
