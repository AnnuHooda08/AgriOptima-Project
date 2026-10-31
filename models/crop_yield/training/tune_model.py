"""Small validation-only decision-tree search after feature and model comparison."""
from pathlib import Path
import json
import sys
import itertools
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train_compare_models import build_candidate, selected_features


def tune_tree():
    """Compare a short grid of leaf sizes and depth limits using only validation years."""
    data = prepare()
    features = selected_features()
    train = data["YearStart"] < 2012
    validation = data["YearStart"].between(2012, 2014)
    results = []
    for max_depth, min_samples_leaf in itertools.product([None, 5, 10], [3, 5, 10, 20]):
        estimator = DecisionTreeRegressor(
            max_depth=max_depth, min_samples_leaf=min_samples_leaf, random_state=42
        )
        model = build_candidate(estimator, features=features).fit(
            data.loc[train, features], data.loc[train, TARGET]
        )
        prediction = model.predict(data.loc[validation, features])
        results.append({
            "max_depth": max_depth if max_depth is not None else "None",
            "min_samples_leaf": min_samples_leaf,
            "validation_mae_t_ha": float(mean_absolute_error(data.loc[validation, TARGET], prediction)),
            "validation_rmse_t_ha": float(np.sqrt(mean_squared_error(data.loc[validation, TARGET], prediction))),
        })
    table = pd.DataFrame(results).sort_values(["validation_mae_t_ha", "validation_rmse_t_ha"])
    output = MODULE / "evaluation"
    table.to_csv(output / "tree_tuning.csv", index=False)
    best = table.iloc[0]
    chosen = {
        "max_depth": None if best["max_depth"] == "None" else int(best["max_depth"]),
        "min_samples_leaf": int(best["min_samples_leaf"]),
    }
    (output / "tree_tuning.json").write_text(json.dumps({
        "search": "max_depth in [None, 5, 10]; min_samples_leaf in [3, 5, 10, 20]",
        "selection": "minimum 2012-2014 validation MAE; RMSE tie-break",
        "features": features,
        "chosen_parameters": chosen,
        "final_test_used_for_tuning": False,
    }, indent=2) + "\n")
    print(table.to_string(index=False))
    print("Selected parameters:", chosen)
    return chosen


if __name__ == "__main__":
    tune_tree()
