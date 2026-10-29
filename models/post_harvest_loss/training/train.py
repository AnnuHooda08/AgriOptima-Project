"""Fit the final categorical Random Forest on all cleaned post-harvest observations."""
from pathlib import Path
import sys
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

MODULE = Path(__file__).resolve().parents[1]
FEATURES = ["state", "crop", "loss_type", "stage"]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import TARGET, prepare

def build_model():
    # One-hot encoding lets the model handle categorical agricultural descriptions.
    preprocessing = ColumnTransformer([
        ("categories", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]), FEATURES),
    ])
    return Pipeline([
        ("preprocessor", preprocessing),
        ("model", RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1
        )),
    ])

def train():
    # Evaluation uses a grouped holdout separately; refit this artifact on all records.
    data = prepare()
    model = build_model().fit(data[FEATURES], data[TARGET])
    artifact = MODULE / "artifacts" / "post_harvest_loss_rf.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, artifact)
    print(f"Trained loss model on {len(data)} records; saved {artifact}")
    return model

if __name__ == "__main__":
    train()
