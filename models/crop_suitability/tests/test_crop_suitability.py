"""Focused checks for preprocessing validation and the existing inference artifact."""

from pathlib import Path
import sys

import joblib
import pandas as pd
import pytest

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "inference"))

from feature_validation import FEATURE_COLUMNS, validate_batch, validate_single_input  # noqa: E402
from predict import ARTIFACT, predict  # noqa: E402


VALID_SAMPLE = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.9,
    "humidity": 82.0,
    "ph": 6.5,
    "rainfall": 202.0,
}


def test_dataset_has_expected_fields_and_labels():
    """The preserved source CSV can be loaded with the documented schema."""
    source = MODULE.parents[1] / "DataSets" / "crop_suitability.csv"
    data = pd.read_csv(source)
    assert list(data.columns) == FEATURE_COLUMNS + ["label"]
    assert data["label"].nunique() == 27
    assert data.isna().sum().sum() == 0


def test_production_artifact_loads_and_contains_its_scaler():
    """The existing model remains a usable scaled pipeline, without rescaling here."""
    pipeline = joblib.load(ARTIFACT)
    assert len(pipeline.classes_) == 27
    assert pipeline.named_steps["standardscaler"] is not None
    assert "rice" in pipeline.classes_


def test_grouped_random_forest_challenger_loads_without_replacing_production():
    """The review candidate is a separate artifact and predicts all known labels."""
    challenger_path = MODULE / "artifacts" / "crop_suitability_grouped_split_challenger_040c3feeea2b.joblib"
    production_path = MODULE / "artifacts" / "crop_suitability_pipeline.pkl"
    challenger = joblib.load(challenger_path)
    production = joblib.load(production_path)
    assert challenger is not production
    assert len(challenger.classes_) == len(production.classes_) == 27
    assert isinstance(challenger.predict(validate_single_input(VALID_SAMPLE))[0], str)


def test_single_input_uses_exact_training_feature_order():
    """Input mapping order cannot accidentally change the model's feature order."""
    shuffled = dict(reversed(list(VALID_SAMPLE.items())))
    row = validate_single_input(shuffled)
    assert list(row.columns) == FEATURE_COLUMNS
    assert row.loc[0, "N"] == 90


def test_prediction_returns_one_crop_label():
    """Inference loads the saved pipeline and returns a plain crop label."""
    result = predict(VALID_SAMPLE)
    assert isinstance(result, str)
    assert result == "rice"


@pytest.mark.parametrize(
    "values, message",
    [
        ({key: value for key, value in VALID_SAMPLE.items() if key != "N"}, "Missing"),
        ({**VALID_SAMPLE, "N": "not a number"}, "must be numeric"),
        ({**VALID_SAMPLE, "N": float("nan")}, "outside the allowed range"),
        ({**VALID_SAMPLE, "humidity": 101}, "outside the allowed range"),
        ({**VALID_SAMPLE, "ph": -1}, "outside the allowed range"),
    ],
)
def test_single_input_rejects_missing_malformed_and_out_of_range_values(values, message):
    """Invalid requests fail clearly instead of reaching the classifier."""
    with pytest.raises(ValueError, match=message):
        validate_single_input(values)


def test_batch_validation_reorders_columns_and_rejects_missing_values():
    """Batch inputs follow the same fixed schema and reject NaN measurements."""
    reversed_columns = list(reversed(FEATURE_COLUMNS))
    data = pd.DataFrame([[VALID_SAMPLE[column] for column in reversed_columns]], columns=reversed_columns)
    validated = validate_batch(data)
    assert list(validated.columns) == FEATURE_COLUMNS

    data.loc[0, "N"] = float("nan")
    with pytest.raises(ValueError, match="NaN"):
        validate_batch(data)


def test_batch_validation_rejects_missing_features():
    """A batch with an omitted required measurement is rejected."""
    data = pd.DataFrame([{key: value for key, value in VALID_SAMPLE.items() if key != "P"}])
    with pytest.raises(ValueError, match="Missing columns"):
        validate_batch(data)
