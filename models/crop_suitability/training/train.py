"""Fit the final SVC classifier for use on future crop suitability requests."""
from pathlib import Path
import sys
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import FEATURES, TARGET, prepare

def build_model():
    # Scaling is essential because soil and weather features use different units.
    return make_pipeline(StandardScaler(), SVC(C=1, kernel="rbf", gamma="scale"))

def train():
    # Refit on every cleaned row after evaluation has measured a held-out split.
    data = prepare()
    model = build_model().fit(data[FEATURES], data[TARGET])
    artifact = MODULE / "artifacts" / "crop_suitability_pipeline.pkl"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact)
    print(f"Trained SVC on {len(data)} rows; saved {artifact}")
    return model

if __name__ == "__main__":
    train()
