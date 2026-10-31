"""Check whether the original numeric features improve validation performance."""
from pathlib import Path
import sys
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train_compare_models import build_candidate


def run_ablation():
    """Compare compact feature sets on 2012-2014 after fitting only through 2011."""
    data = prepare()
    train = data["YearStart"] < 2012
    validation = data["YearStart"].between(2012, 2014)
    groups = {
        "all six inputs": FEATURES,
        "without Area": [feature for feature in FEATURES if feature != "Area"],
        "without YearStart": [feature for feature in FEATURES if feature != "YearStart"],
        "without Area and YearStart": [
            feature for feature in FEATURES if feature not in {"Area", "YearStart"}
        ],
        "Crop and Season only": ["Crop", "Season"],
    }
    rows = []
    for label, features in groups.items():
        model = build_candidate(Ridge(alpha=10.0), features=features)
        model.fit(data.loc[train, features], data.loc[train, TARGET])
        prediction = model.predict(data.loc[validation, features])
        rows.append({
            "feature_set": label,
            "features": ", ".join(features),
            "validation_mae_t_ha": float(mean_absolute_error(data.loc[validation, TARGET], prediction)),
            "validation_rmse_t_ha": float(np.sqrt(mean_squared_error(data.loc[validation, TARGET], prediction))),
        })
    table = pd.DataFrame(rows).sort_values("validation_mae_t_ha")
    table.to_csv(MODULE / "evaluation/feature_ablation_validation.csv", index=False)
    print(table.to_string(index=False))
    return table


if __name__ == "__main__":
    run_ablation()
