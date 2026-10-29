"""Compare a chronological price holdout against persistence and seasonal baselines."""
from pathlib import Path
import json
import sys
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

MODULE = Path(__file__).resolve().parents[1]
FEATURES = ["lag_1", "lag_2", "lag_3", "lag_12", "month", "year"]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import prepare
sys.path.insert(0, str(MODULE / "training"))
from train import build_model

def evaluate():
    # Train only on records before 2021 and leave 2023 onward untouched for testing.
    data = prepare()
    train_rows = data["date"] < "2021-01-01"
    test_rows = data["date"] >= "2023-01-01"
    if not train_rows.any() or not test_rows.any():
        raise ValueError("Need pre-2021 training months and 2023+ test months.")
    model = build_model().fit(data.loc[train_rows, FEATURES], data.loc[train_rows, "price"])
    test = data.loc[test_rows]
    predictions = model.predict(test[FEATURES])
    baselines = {
        "previous_calendar_month": test["lag_1"].to_numpy(),
        "same_month_previous_year": test["lag_12"].to_numpy(),
        "hist_gradient_boosting": predictions,
    }
    result = {
        "split": "train before 2021; test 2023 onward; missing calendar months excluded",
        "train_rows": int(train_rows.sum()),
        "test_rows": int(test_rows.sum()),
        "test_month_min": str(test["date"].min().date()),
        "test_month_max": str(test["date"].max().date()),
        "metrics": {},
    }
    for name, values in baselines.items():
        result["metrics"][name] = {
            "mae_rs_per_quintal": float(mean_absolute_error(test["price"], values)),
            "rmse_rs_per_quintal": float(np.sqrt(mean_squared_error(test["price"], values))),
        }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate()
