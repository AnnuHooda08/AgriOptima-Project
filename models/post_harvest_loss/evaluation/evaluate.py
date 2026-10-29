"""Evaluate loss regression on held-out state/crop groups against a median baseline."""
from pathlib import Path
import json
import sys
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error

MODULE = Path(__file__).resolve().parents[1]
FEATURES = ["state", "crop", "loss_type", "stage"]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import TARGET, prepare
sys.path.insert(0, str(MODULE / "training"))
from train import build_model

def evaluate():
    # Keep all stages for a state/crop pair in one partition to reduce record leakage.
    data = prepare()
    groups = data["state"] + "|" + data["crop"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(splitter.split(data, groups=groups))
    train, test = data.iloc[train_idx], data.iloc[test_idx]
    model = build_model().fit(train[FEATURES], train[TARGET])
    prediction = model.predict(test[FEATURES])
    baseline = np.repeat(train[TARGET].median(), len(test))
    result = {
        "split": "group holdout by state and crop; random_state=42",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "held_out_groups": int(groups.iloc[test_idx].nunique()),
        "target_unit": "percentage points",
        "median_baseline_mae": float(mean_absolute_error(test[TARGET], baseline)),
        "random_forest_mae": float(mean_absolute_error(test[TARGET], prediction)),
        "random_forest_rmse": float(np.sqrt(mean_squared_error(test[TARGET], prediction))),
    }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate()
