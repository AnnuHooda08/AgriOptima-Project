"""Train and save a readable one-step-ahead Linear Regression pipeline."""

from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_linear_data import load_model_data


ARTIFACT = MODULE / "artifacts" / "maize_price_linear_regression.joblib"
FEATURES = ["lag_1", "lag_2", "lag_3", "lag_12", "month", "year"]
NUMERIC_FEATURES = ["lag_1", "lag_2", "lag_3", "lag_12", "year"]
CATEGORICAL_FEATURES = ["month"]


def build_pipeline() -> Pipeline:
    """Make a simple regression pipeline with training-only preprocessing."""
    preprocess = ColumnTransformer(
        transformers=[
            # A month is a season category, not a straight-line quantity.
            ("month", OneHotEncoder(categories=[list(range(1, 13))], drop="first", handle_unknown="ignore"), CATEGORICAL_FEATURES),
            # This imputer is fitted inside the Pipeline on training rows only.
            ("numeric", SimpleImputer(strategy="median", keep_empty_features=True), NUMERIC_FEATURES),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("regression", LinearRegression()),
        ]
    )


def train() -> Pipeline:
    """Fit the approved production candidate only on data before the test period."""
    data = load_model_data()
    # The final 2023+ test period is not included in the saved model artifact.
    training_rows = data["date"] < "2023-01-01"
    if training_rows.sum() < 24:
        raise ValueError("At least two years of pre-test monthly data are required.")
    model = build_pipeline().fit(data.loc[training_rows, FEATURES], data.loc[training_rows, "price"])

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "target": "monthly maize modal price (Rs/quintal)",
            "training_first_month": str(data.loc[training_rows, "date"].min().date()),
            "training_last_month": str(data.loc[training_rows, "date"].max().date()),
            "forecast_horizon": "one month ahead; user supplies latest observed calendar lags",
        },
        ARTIFACT,
    )

    # Save the learned month and numeric coefficients in a readable table for viva.
    feature_names = model.named_steps["preprocess"].get_feature_names_out()
    coefficients = model.named_steps["regression"].coef_
    report_dir = MODULE / "evaluation" / "reports" / "linear_regression"
    report_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"feature": feature_names, "coefficient": coefficients}).to_csv(
        report_dir / "linear_regression_coefficients.csv", index=False
    )
    print(f"Trained Linear Regression on {int(training_rows.sum())} pre-test monthly rows; saved {ARTIFACT}")
    return model


if __name__ == "__main__":
    train()
