"""Compare simple regression candidates using an earlier chronological validation period."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
from prepare_data import FEATURES, TARGET, prepare

CATEGORICAL = ["State", "District", "Crop", "Season"]
NUMERICAL = ["YearStart", "Area"]
VALIDATION_START = 2012
def selected_features():
    """Use the validation-only ablation winner when available; otherwise use the full baseline set."""
    ablation_file = MODULE / "evaluation/feature_ablation_validation.csv"
    if not ablation_file.exists():
        return list(FEATURES)
    ablation = pd.read_csv(ablation_file).sort_values(
        ["validation_mae_t_ha", "validation_rmse_t_ha"]
    )
    return str(ablation.iloc[0]["features"]).split(", ")


def build_candidate(estimator, features=FEATURES):
    """Keep preprocessing inside each estimator so it fits only on training years."""
    categorical = [column for column in CATEGORICAL if column in features]
    numerical = [column for column in NUMERICAL if column in features]
    transform = ColumnTransformer([
        ("categories", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
        ("numbers", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numerical),
    ])
    return Pipeline([("preprocess", transform), ("model", estimator)])


def candidates():
    """Return the five requested, modestly sized regression algorithms."""
    tree_parameters = {"max_depth": None, "min_samples_leaf": 3}
    tuning_file = MODULE / "evaluation/tree_tuning.json"
    if tuning_file.exists():
        tree_parameters.update(json.loads(tuning_file.read_text()).get("chosen_parameters", {}))
    return {
        "Linear Regression": LinearRegression(),
        "Ridge": Ridge(alpha=10.0),
        "Lasso": Lasso(alpha=0.001, max_iter=10000, random_state=42),
        "Decision Tree": DecisionTreeRegressor(**tree_parameters, random_state=42),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_leaf=3, random_state=42, n_jobs=1
        ),
    }


def score(actual, predicted):
    """Calculate familiar regression measures in the target's tonnes/hectare unit."""
    return {
        "mae_t_ha": float(mean_absolute_error(actual, predicted)),
        "rmse_t_ha": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def compare_models():
    """Choose by validation MAE, then evaluate candidates once on the later test years."""
    data = prepare()
    features = selected_features()
    train_mask = data["YearStart"] < VALIDATION_START
    validation_mask = data["YearStart"].between(VALIDATION_START, 2014)
    test_mask = data["YearStart"] >= 2015
    if not train_mask.any() or not validation_mask.any() or not test_mask.any():
        raise ValueError("Need training years before 2012, validation 2012–2014 and test 2015+.")
    rows = []
    # Validation scores select; final-test scores describe held-out generalization.
    for name, estimator in candidates().items():
        model = build_candidate(estimator, features=features).fit(data.loc[train_mask, features], data.loc[train_mask, TARGET])
        val_prediction = model.predict(data.loc[validation_mask, features])
        # Refit on all pre-test years after validation-only model selection.
        test_model = build_candidate(estimator, features=features).fit(data.loc[~test_mask, features], data.loc[~test_mask, TARGET])
        test_prediction = test_model.predict(data.loc[test_mask, features])
        rows.append({
            "model": name,
            **{f"validation_{k}": v for k, v in score(data.loc[validation_mask, TARGET], val_prediction).items()},
            **{f"test_{k}": v for k, v in score(data.loc[test_mask, TARGET], test_prediction).items()},
        })
    table = pd.DataFrame(rows).sort_values(["validation_mae_t_ha", "validation_rmse_t_ha"])
    # This winner is selected from validation only, never from final test scores.
    selected = str(table.iloc[0]["model"])
    # Shuffle one original field at a time on validation records to estimate its
    # contribution to MAE without exposing the final test set to feature selection.
    selected_estimator = candidates()[selected]
    if selected == "Ridge":
        selected_estimator = Ridge(alpha=10.0)
    validation_model = build_candidate(selected_estimator, features=features).fit(
        data.loc[train_mask, features], data.loc[train_mask, TARGET]
    )
    importance = permutation_importance(
        validation_model,
        data.loc[validation_mask, features],
        data.loc[validation_mask, TARGET],
        scoring="neg_mean_absolute_error",
        n_repeats=5,
        random_state=42,
        n_jobs=1,
    )
    importance_table = pd.DataFrame({
        "feature": features,
        "mae_increase_when_shuffled_t_ha": importance.importances_mean,
        "repeat_std_t_ha": importance.importances_std,
    }).sort_values("mae_increase_when_shuffled_t_ha", ascending=False)
    output = MODULE / "evaluation"
    output.mkdir(parents=True, exist_ok=True)
    table.to_csv(output / "model_comparison.csv", index=False)
    importance_table.to_csv(output / "feature_importance_validation.csv", index=False)
    selected_parameters = {}
    tree_tuning_file = output / "tree_tuning.json"
    if selected == "Decision Tree" and tree_tuning_file.exists():
        selected_parameters = json.loads(tree_tuning_file.read_text())["chosen_parameters"]
    elif selected == "Ridge":
        selected_parameters = {"alpha": 10.0}
    elif selected == "Lasso":
        selected_parameters = {"alpha": 0.001}
    (output / "model_selection.json").write_text(json.dumps({
        "selection_rule": "lowest MAE on 2012–2014 validation; RMSE used as tie-breaker",
        "train_years": f"{int(data.loc[train_mask, 'YearStart'].min())}-{int(data.loc[train_mask, 'YearStart'].max())}",
        "validation_years": "2012-2014",
        "test_years": f"{int(data.loc[test_mask, 'YearStart'].min())}-{int(data.loc[test_mask, 'YearStart'].max())}",
        "selected_model": selected,
        "selected_features": features,
        "selected_parameters": selected_parameters,
        "train_rows": int(train_mask.sum()),
        "validation_rows": int(validation_mask.sum()),
        "test_rows": int(test_mask.sum()),
    }, indent=2) + "\n")
    print(table.to_string(index=False))
    print(f"Selected from validation only: {selected}")
    return table, selected


if __name__ == "__main__":
    compare_models()
