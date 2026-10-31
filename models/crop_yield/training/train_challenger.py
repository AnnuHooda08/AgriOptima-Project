"""Fit the validation-selected challenger without replacing the current API artifact."""
from pathlib import Path
import json
import sys
import joblib
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import Ridge

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train_compare_models import build_candidate, candidates


def train_challenger():
    """Train selected model on all clean observations and save a distinct artifact."""
    selection = json.loads((MODULE / "evaluation/model_selection.json").read_text())
    name = selection["selected_model"]
    if name == "Ridge":
        estimator = Ridge(alpha=float(selection.get("selected_parameters", {}).get("alpha", 10.0)))
    elif name == "Decision Tree":
        estimator = DecisionTreeRegressor(
            **selection.get("selected_parameters", {"max_depth": None, "min_samples_leaf": 3}),
            random_state=42
        )
    else:
        estimator = candidates()[name]
    data = prepare()
    features = selection.get("selected_features", FEATURES)
    pipeline = build_candidate(estimator, features=features).fit(data[features], data[TARGET])
    feature_tag = "_crop_season" if features == ["Crop", "Season"] else ""
    output = MODULE / "artifacts" / f"challenger_{name.lower().replace(' ', '_')}{feature_tag}.joblib"
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output)
    print(f"Saved {name} challenger on {len(data)} clean rows to {output}")
    return output


if __name__ == "__main__":
    train_challenger()
