"""Measure yield forecasts on years deliberately held out from model fitting."""
from pathlib import Path
import json
import sys
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train import build_model

def evaluate():
    # Keep every year from 2015 onward out of model fitting.
    data = prepare()
    train_rows = data["YearStart"] < 2015
    test_rows = ~train_rows
    if not train_rows.any() or not test_rows.any():
        raise ValueError("Both pre-2015 training rows and 2015+ test rows are required.")
    model = build_model().fit(data.loc[train_rows, FEATURES], data.loc[train_rows, TARGET])
    actual = data.loc[test_rows, TARGET]
    predicted = model.predict(data.loc[test_rows, FEATURES])
    baseline = np.repeat(data.loc[train_rows, TARGET].median(), len(actual))
    result = {
        "split": "train before 2015; test 2015 onward",
        "train_rows": int(train_rows.sum()),
        "test_rows": int(test_rows.sum()),
        "test_year_min": int(data.loc[test_rows, "YearStart"].min()),
        "test_year_max": int(data.loc[test_rows, "YearStart"].max()),
        "random_forest_mae": float(mean_absolute_error(actual, predicted)),
        "median_baseline_mae": float(mean_absolute_error(actual, baseline)),
        "random_forest_rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "random_forest_r2": float(r2_score(actual, predicted)),
    }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate()
