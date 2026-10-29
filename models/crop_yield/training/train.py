"""Fit the deployable Random Forest on the complete cleaned yield history."""
from pathlib import Path
import sys
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import FEATURES, TARGET, prepare

CATEGORICAL = ["State", "District", "Crop", "Season"]
NUMERICAL = ["YearStart", "Area"]

def build_model():
    # Encode categories safely and standardize numeric columns in one saved pipeline.
    preprocessing = ColumnTransformer([
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL),
        ("numerical", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), NUMERICAL),
    ])
    return Pipeline([
        ("preprocessor", preprocessing),
        ("model", RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_leaf=3,
            random_state=42, n_jobs=1,
        )),
    ])

def train():
    # Evaluation is performed separately; this production artifact can then use all rows.
    data = prepare()
    model = build_model().fit(data[FEATURES], data[TARGET])
    artifact = MODULE / "artifacts" / "random_forest.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact)
    print(f"Trained Random Forest on all {len(data)} clean records; saved {artifact}")
    return model

if __name__ == "__main__":
    train()
