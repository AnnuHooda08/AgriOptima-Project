"""Validate seven crop suitability inputs and predict a crop label."""
from pathlib import Path
import sys
import joblib

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
from feature_validation import validate_single_input
ARTIFACT = MODULE / "artifacts" / "crop_suitability_pipeline.pkl"

def predict(values):
    # Reuse the shared range and type checks before calling the saved pipeline.
    row = validate_single_input(values)
    return str(joblib.load(ARTIFACT).predict(row)[0])

if __name__ == "__main__":
    sample = dict(N=90, P=42, K=43, temperature=20, humidity=80, ph=6.5, rainfall=200)
    print("Predicted crop:", predict(sample))
