"""Load a saved yield pipeline and validate farmer-provided fields before prediction."""
from pathlib import Path
import math
import joblib
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ARTIFACT = MODULE / "artifacts" / "random_forest.joblib"
FEATURES = ["State", "District", "Crop", "Season", "YearStart", "Area"]
CATEGORY_COLUMNS = ["State", "District", "Crop", "Season"]


def _category_values(pipeline):
    """Read the categories learned for the categorical columns in this pipeline."""
    preprocessor = pipeline.named_steps.get("preprocessor", pipeline.named_steps.get("preprocess"))
    if preprocessor is None:
        raise ValueError("Saved model does not include its expected preprocessing pipeline.")
    category_transformer = None
    for key in ("categorical", "categories"):
        if key in preprocessor.named_transformers_:
            category_transformer = preprocessor.named_transformers_[key]
            break
    if category_transformer is None:
        return {}
    encoder = None
    for step_name in ("encoder", "one_hot"):
        if step_name in category_transformer.named_steps:
            encoder = category_transformer.named_steps[step_name]
            break
    if encoder is None:
        raise ValueError("Saved model is missing its one-hot encoder.")
    category_columns = next(
        columns for name, _, columns in preprocessor.transformers_ if name in ("categorical", "categories")
    )
    return {
        column: {str(value) for value in values}
        for column, values in zip(category_columns, encoder.categories_)
    }


def predict(values, artifact_path=ARTIFACT):
    """Return tonnes/hectare; fail clearly on incomplete or unsupported requests."""
    if not isinstance(values, dict):
        raise ValueError("Yield input must be a dictionary of named fields.")
    pipeline = joblib.load(artifact_path)
    features = list(getattr(pipeline, "feature_names_in_", FEATURES))
    missing = [name for name in features if name not in values or values[name] is None]
    if missing:
        raise ValueError(f"Missing yield inputs: {missing}")
    known = _category_values(pipeline)
    canonical = dict(values)
    for column in features:
        if column not in CATEGORY_COLUMNS:
            continue
        value = values[column]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{column} must be a non-empty text value.")
        matches = {label.casefold(): label for label in known[column]}
        key = value.strip().casefold()
        if key not in matches:
            raise ValueError(f"Unknown {column} value {value!r}; use a category in the supported dataset.")
        canonical[column] = matches[key]
    if "YearStart" in features:
        try:
            year = float(values["YearStart"])
        except (TypeError, ValueError) as exc:
            raise ValueError("YearStart must be numeric.") from exc
        if not math.isfinite(year) or year != int(year) or not 1900 <= year <= 2100:
            raise ValueError("YearStart must be a whole year between 1900 and 2100.")
    if "Area" in features:
        try:
            area = float(values["Area"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Area must be numeric.") from exc
        if not math.isfinite(area) or area <= 0:
            raise ValueError("Area must be a finite positive number of hectares.")
    row = pd.DataFrame([{name: canonical[name] for name in features}])
    prediction = float(pipeline.predict(row)[0])
    if not math.isfinite(prediction) or prediction < 0:
        raise ValueError("The saved model returned an invalid yield estimate.")
    return prediction


if __name__ == "__main__":
    example = dict(State="Punjab", District="Ludhiana", Crop="Wheat",
                   Season="Rabi", YearStart=2024, Area=1000)
    print(f"Predicted yield: {predict(example):.3f} tonnes per hectare")
