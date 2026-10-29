"""Fit the final experimental maize price model on all valid monthly data."""
from pathlib import Path
import sys
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor

MODULE = Path(__file__).resolve().parents[1]
FEATURES = ["lag_1", "lag_2", "lag_3", "lag_12", "month", "year"]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import prepare

def build_model():
    # Small tree leaves reduce variance on this short aggregate time series.
    return HistGradientBoostingRegressor(
        max_iter=100, learning_rate=0.05, max_leaf_nodes=15,
        l2_regularization=1, random_state=42,
    )

def train():
    # The independent chronological benchmark is in evaluation/evaluate.py.
    data = prepare()
    model = build_model().fit(data[FEATURES], data["price"])
    artifact = MODULE / "artifacts" / "maize_price_hgb.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, artifact)
    print(f"Trained experimental price model on {len(data)} monthly rows; saved {artifact}")
    return model

if __name__ == "__main__":
    train()
