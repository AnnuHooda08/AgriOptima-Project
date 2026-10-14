
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_DIR / "data" / "processed" / "crop_yield_model_data.csv"
MODEL_DIR = PROJECT_DIR / "models"
REPORT_DIR = PROJECT_DIR / "reports"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Yield"

CATEGORICAL_FEATURES = ["State", "District", "Crop", "Season"]
NUMERICAL_FEATURES = ["YearStart", "Area"]
FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

TEST_START_YEAR = 2015


# --------------------------------------------------
# 2. Load and validate data
# --------------------------------------------------
df = pd.read_csv(DATA_FILE)

required = FEATURES + [TARGET]
missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

if df[required].isna().any().any():
    raise ValueError("Missing values found in model data.")

if (df[TARGET] <= 0).any():
    raise ValueError("Non-positive target values found.")

# Keep later years entirely outside training.
train = df[df["YearStart"] < TEST_START_YEAR].copy()
test = df[df["YearStart"] >= TEST_START_YEAR].copy()

if train.empty or test.empty:
    raise ValueError("Training or test dataset is empty.")

X_train = train[FEATURES]
y_train = train[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]

print("TRAINING AND TEST DATA")
print("-" * 50)
print("Training rows:", len(train))
print("Training years:", train["YearStart"].min(), "-", train["YearStart"].max())
print("Test rows:", len(test))
print("Test years:", test["YearStart"].min(), "-", test["YearStart"].max())
print("Features:", FEATURES)


# --------------------------------------------------
# 3. Preprocessing
# --------------------------------------------------
# Fit preprocessing on training data only.
categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

preprocessor = ColumnTransformer([
    ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ("numerical", numerical_pipeline, NUMERICAL_FEATURES),
])


# --------------------------------------------------
# 4. Define regression models
# --------------------------------------------------
models = {
    "Linear Regression": LinearRegression(),

    "Ridge Regression": Ridge(alpha=1.0),

    "Lasso Regression": Lasso(alpha=0.01, max_iter=20000),

    "Decision Tree": DecisionTreeRegressor(
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
    ),

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
}


# --------------------------------------------------
# 5. Train, evaluate, and save
# --------------------------------------------------
results = []
prediction_output = test[
    ["State", "District", "Crop", "Season", "YearStart", "Yield"]
].copy()

for name, estimator in models.items():
    print(f"\nTraining {name}...")

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    results.append({
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    safe_name = name.lower().replace(" ", "_")
    joblib.dump(pipeline, MODEL_DIR / f"{safe_name}.joblib")

    prediction_output[f"Predicted_{safe_name}"] = predictions

    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R2:   {r2:.4f}")


# --------------------------------------------------
# 6. Save comparison reports
# --------------------------------------------------
results_df = pd.DataFrame(results).sort_values("MAE")

results_file = REPORT_DIR / "model_comparison.csv"
predictions_file = REPORT_DIR / "test_predictions.csv"

results_df.to_csv(results_file, index=False)
prediction_output.to_csv(predictions_file, index=False)

print("\nMODEL COMPARISON")
print("-" * 50)
print(results_df.to_string(index=False))

print("\nBest model by MAE:", results_df.iloc[0]["Model"])
print("Comparison saved:", results_file)
print("Test predictions saved:", predictions_file)
print("Trained models saved in:", MODEL_DIR)

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_DIR / "data" / "processed" / "crop_yield_model_data.csv"
MODEL_DIR = PROJECT_DIR / "models"
REPORT_DIR = PROJECT_DIR / "reports"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Yield"

CATEGORICAL_FEATURES = ["State", "District", "Crop", "Season"]
NUMERICAL_FEATURES = ["YearStart", "Area"]
FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

TEST_START_YEAR = 2015


# --------------------------------------------------
# 2. Load and validate data
# --------------------------------------------------
df = pd.read_csv(DATA_FILE)

required = FEATURES + [TARGET]
missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

if df[required].isna().any().any():
    raise ValueError("Missing values found in model data.")

if (df[TARGET] <= 0).any():
    raise ValueError("Non-positive target values found.")

# Keep later years entirely outside training.
train = df[df["YearStart"] < TEST_START_YEAR].copy()
test = df[df["YearStart"] >= TEST_START_YEAR].copy()

if train.empty or test.empty:
    raise ValueError("Training or test dataset is empty.")

X_train = train[FEATURES]
y_train = train[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]

print("TRAINING AND TEST DATA")
print("-" * 50)
print("Training rows:", len(train))
print("Training years:", train["YearStart"].min(), "-", train["YearStart"].max())
print("Test rows:", len(test))
print("Test years:", test["YearStart"].min(), "-", test["YearStart"].max())
print("Features:", FEATURES)


# --------------------------------------------------
# 3. Preprocessing
# --------------------------------------------------
# Fit preprocessing on training data only.
categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

preprocessor = ColumnTransformer([
    ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ("numerical", numerical_pipeline, NUMERICAL_FEATURES),
])


# --------------------------------------------------
# 4. Define regression models
# --------------------------------------------------
models = {
    "Linear Regression": LinearRegression(),

    "Ridge Regression": Ridge(alpha=1.0),

    "Lasso Regression": Lasso(alpha=0.01, max_iter=20000),

    "Decision Tree": DecisionTreeRegressor(
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
    ),

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
}


# --------------------------------------------------
# 5. Train, evaluate, and save
# --------------------------------------------------
results = []
prediction_output = test[
    ["State", "District", "Crop", "Season", "YearStart", "Yield"]
].copy()

for name, estimator in models.items():
    print(f"\nTraining {name}...")

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    results.append({
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    safe_name = name.lower().replace(" ", "_")
    joblib.dump(pipeline, MODEL_DIR / f"{safe_name}.joblib")

    prediction_output[f"Predicted_{safe_name}"] = predictions

    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R2:   {r2:.4f}")


# --------------------------------------------------
# 6. Save comparison reports
# --------------------------------------------------
results_df = pd.DataFrame(results).sort_values("MAE")

results_file = REPORT_DIR / "model_comparison.csv"
predictions_file = REPORT_DIR / "test_predictions.csv"

results_df.to_csv(results_file, index=False)
prediction_output.to_csv(predictions_file, index=False)

print("\nMODEL COMPARISON")
print("-" * 50)
print(results_df.to_string(index=False))

print("\nBest model by MAE:", results_df.iloc[0]["Model"])
print("Comparison saved:", results_file)
print("Test predictions saved:", predictions_file)
print("Trained models saved in:", MODEL_DIR)
