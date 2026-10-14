
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "crop_yield_model_data.csv"
)

REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

target = "Yield"
categorical = ["State", "District", "Crop", "Season"]
numerical = ["YearStart", "Area"]
features = categorical + numerical

# Chronological validation within the original training period.
train = df[df["YearStart"] <= 2009].copy()
valid = df[
    (df["YearStart"] >= 2010)
    & (df["YearStart"] <= 2014)
].copy()

X_train = train[features]
y_train = train[target]

X_valid = valid[features]
y_valid = valid[target]

print("TEMPORAL VALIDATION")
print("-" * 60)
print("Training years:", train["YearStart"].min(), "-", train["YearStart"].max())
print("Training rows:", len(train))
print("Validation years:", valid["YearStart"].min(), "-", valid["YearStart"].max())
print("Validation rows:", len(valid))

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical,
        ),
        (
            "numerical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]),
            numerical,
        ),
    ]
)

results = []
prediction_data = valid[
    ["State", "District", "Crop", "Season", "YearStart", "Yield"]
].copy()

for use_log in [False, True]:
    model = Pipeline([
        ("preprocessor", preprocessor),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ])

    model_target = np.log1p(y_train) if use_log else y_train

    model.fit(X_train, model_target)

    predictions = model.predict(X_valid)

    if use_log:
        predictions = np.expm1(predictions)

    # Yield cannot be negative.
    predictions = np.maximum(predictions, 0)

    errors = y_valid.to_numpy() - predictions

    results.append({
        "Target_Transformation": (
            "log1p" if use_log else "original"
        ),
        "MAE": mean_absolute_error(y_valid, predictions),
        "RMSE": np.sqrt(mean_squared_error(y_valid, predictions)),
        "R2": r2_score(y_valid, predictions),
        "Median_Absolute_Error": np.median(np.abs(errors)),
        "90th_Percentile_Absolute_Error": np.quantile(
            np.abs(errors), 0.90
        ),
    })

    prediction_data[
        "Predicted_log" if use_log else "Predicted_original"
    ] = predictions

results_df = pd.DataFrame(results).sort_values("MAE")

print("\nVALIDATION MODEL COMPARISON")
print("-" * 60)
print(results_df.round(4).to_string(index=False))

results_df.to_csv(
    REPORT_DIR / "log_target_validation_comparison.csv",
    index=False,
)

prediction_data.to_csv(
    REPORT_DIR / "log_target_validation_predictions.csv",
    index=False,
)

print("\nSaved:")
print(REPORT_DIR / "log_target_validation_comparison.csv")
print(REPORT_DIR / "log_target_validation_predictions.csv")
