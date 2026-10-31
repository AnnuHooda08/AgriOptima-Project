"""Validation-only comparison of yield models, feature sets, errors, and time windows."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.tree import plot_tree

MODULE = Path(__file__).resolve().parents[1]
OUT = MODULE / "evaluation" / "review"
PLOTS = OUT / "plots"
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train_compare_models import build_candidate, candidates

# A, B, and C are all supported by columns present in the primary source.
FEATURE_CONFIGS = {
    "A_crop_season": ["Crop", "Season"],
    "B_all_six": FEATURES,
    "C_crop_season_year_area": ["Crop", "Season", "YearStart", "Area"],
}


def metrics(actual, predicted):
    """Return standard regression metrics in tonnes/hectare."""
    return {
        "mae_t_ha": float(mean_absolute_error(actual, predicted)),
        "rmse_t_ha": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def fit_prediction(data, train_mask, validation_mask, feature_list, estimator):
    """Fit all preprocessing on earlier rows, then predict the later rows."""
    model = build_candidate(estimator, features=feature_list)
    model.fit(data.loc[train_mask, feature_list], data.loc[train_mask, TARGET])
    return model, model.predict(data.loc[validation_mask, feature_list])


def run_review():
    """Generate comparisons without reading final-test years or changing artifacts."""
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    data = prepare()
    train_mask = data["YearStart"] < 2012
    validation_mask = data["YearStart"].between(2012, 2014)
    train, validation = data.loc[train_mask], data.loc[validation_mask]
    rows = []
    selected_tree = None

    # Every candidate sees the same 1997-2011 training and 2012-2014 validation records.
    for config_name, feature_list in FEATURE_CONFIGS.items():
        for model_name, estimator in candidates().items():
            model, prediction = fit_prediction(
                data, train_mask, validation_mask, feature_list, estimator
            )
            rows.append({
                "feature_config": config_name,
                "features": ", ".join(feature_list),
                "model": model_name,
                **metrics(validation[TARGET], prediction),
            })
            if config_name == "A_crop_season" and model_name == "Decision Tree":
                selected_tree = model, prediction, feature_list

    comparison = pd.DataFrame(rows).sort_values(
        ["feature_config", "mae_t_ha", "rmse_t_ha"]
    )
    comparison.to_csv(OUT / "validation_model_feature_comparison.csv", index=False)

    # Training-versus-validation performance and tree structure expose overfitting.
    tree_model, tree_prediction, tree_features = selected_tree
    tree_train_prediction = tree_model.predict(train[tree_features])
    tree = tree_model.named_steps["model"]
    tree_summary = {
        "feature_config": "A_crop_season",
        "features": tree_features,
        "parameters": tree.get_params(),
        "tree_depth": int(tree.tree_.max_depth),
        "tree_nodes": int(tree.tree_.node_count),
        "tree_leaves": int(tree.tree_.n_leaves),
        "train_rows": int(train_mask.sum()),
        "validation_rows": int(validation_mask.sum()),
        "train_metrics": metrics(train[TARGET], tree_train_prediction),
        "validation_metrics": metrics(validation[TARGET], tree_prediction),
    }
    (OUT / "decision_tree_complexity.json").write_text(json.dumps(tree_summary, indent=2) + "\n")

    # Preserve individual errors for direct review of outliers and group behavior.
    errors = validation[
        ["State", "District", "Crop", "Season", "YearStart", TARGET]
    ].copy()
    errors["predicted_yield_t_ha"] = tree_prediction
    errors["residual_t_ha"] = errors[TARGET] - errors["predicted_yield_t_ha"]
    errors["absolute_error_t_ha"] = errors["residual_t_ha"].abs()
    errors.to_csv(OUT / "decision_tree_validation_predictions.csv", index=False)

    def group_errors(column):
        return errors.groupby(column).agg(
            records=(TARGET, "size"),
            actual_mean_t_ha=(TARGET, "mean"),
            predicted_mean_t_ha=("predicted_yield_t_ha", "mean"),
            mae_t_ha=("absolute_error_t_ha", "mean"),
            rmse_t_ha=("residual_t_ha", lambda v: float(np.sqrt(np.mean(v ** 2)))),
            mean_residual_t_ha=("residual_t_ha", "mean"),
        ).sort_values("records", ascending=False)

    group_errors("Crop").to_csv(OUT / "decision_tree_errors_by_crop.csv")
    group_errors("State").to_csv(OUT / "decision_tree_errors_by_state.csv")
    group_errors("District").to_csv(OUT / "decision_tree_errors_by_district.csv")
    group_errors("Season").to_csv(OUT / "decision_tree_errors_by_season.csv")
    errors.nlargest(30, "absolute_error_t_ha").to_csv(
        OUT / "decision_tree_largest_validation_errors.csv", index=False
    )

    # Compare high-yield Sugarcane errors with all other validation crops.
    is_sugarcane = errors["Crop"].str.casefold().eq("sugarcane")
    sugar = errors.loc[is_sugarcane]
    other = errors.loc[~is_sugarcane]
    sugar_summary = {
        "sugarcane_records": int(len(sugar)),
        "other_records": int(len(other)),
        "sugarcane_actual_mean_t_ha": float(sugar[TARGET].mean()),
        "sugarcane_predicted_mean_t_ha": float(sugar["predicted_yield_t_ha"].mean()),
        "sugarcane_mae_t_ha": float(sugar["absolute_error_t_ha"].mean()),
        "other_crop_mae_t_ha": float(other["absolute_error_t_ha"].mean()),
        "sugarcane_p95_absolute_error_t_ha": float(sugar["absolute_error_t_ha"].quantile(.95)),
        "sugarcane_largest_errors": sugar.nlargest(
            10, "absolute_error_t_ha"
        ).to_dict(orient="records"),
    }
    (OUT / "sugarcane_sensitivity.json").write_text(json.dumps(sugar_summary, indent=2) + "\n")

    # Rolling-origin checks use only years before the untouched 2015-2019 final test.
    windows = [("2006-2008", 2006, 2008), ("2009-2011", 2009, 2011), ("2012-2014", 2012, 2014)]
    robustness = []
    for period, start, end in windows:
        earlier_train = data["YearStart"] < start
        heldout = data["YearStart"].between(start, end)
        for config_name, feature_list in FEATURE_CONFIGS.items():
            for model_name, estimator in candidates().items():
                _, prediction = fit_prediction(
                    data, earlier_train, heldout, feature_list, estimator
                )
                robustness.append({
                    "validation_period": period,
                    "feature_config": config_name,
                    "model": model_name,
                    "train_rows": int(earlier_train.sum()),
                    "validation_rows": int(heldout.sum()),
                    **metrics(data.loc[heldout, TARGET], prediction),
                })
    robustness_table = pd.DataFrame(robustness)
    robustness_table.to_csv(OUT / "rolling_validation_robustness.csv", index=False)
    winners = robustness_table.sort_values(
        ["validation_period", "mae_t_ha", "rmse_t_ha"]
    ).groupby("validation_period", as_index=False).first()
    winners.to_csv(OUT / "rolling_validation_winners.csv", index=False)

    # Save readable validation-only diagnostic plots.
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(errors[TARGET], errors["predicted_yield_t_ha"], alpha=.4)
    limit = max(errors[TARGET].max(), errors["predicted_yield_t_ha"].max())
    ax.plot([0, limit], [0, limit], color="red", linestyle="--")
    ax.set(title="Decision Tree validation: actual vs predicted",
           xlabel="Actual yield (tonnes/hectare)", ylabel="Predicted yield (tonnes/hectare)")
    fig.tight_layout()
    fig.savefig(PLOTS / "decision_tree_actual_vs_predicted.png", dpi=160)
    plt.close(fig)

    crop_errors = group_errors("Crop").sort_values("mae_t_ha", ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(10, 7))
    crop_errors["mae_t_ha"].sort_values().plot(kind="barh", ax=ax)
    ax.set(title="Highest crop-wise Decision Tree validation MAE",
           xlabel="MAE (tonnes/hectare)", ylabel="Crop")
    fig.tight_layout()
    fig.savefig(PLOTS / "decision_tree_error_by_crop.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 7))
    plot_tree(
        tree,
        feature_names=tree_model.named_steps["preprocess"].get_feature_names_out(),
        filled=True,
        max_depth=3,
        fontsize=7,
        ax=ax,
    )
    ax.set_title("Decision Tree, first three levels")
    fig.tight_layout()
    fig.savefig(PLOTS / "decision_tree_structure_depth3.png", dpi=160)
    plt.close(fig)

    summary = {
        "main_split": "Train before 2012; validate 2012-2014",
        "final_test_used": False,
        "feature_configurations": {
            "A_crop_season": "Crop-season typical yield, without district/year/farm-area distinctions.",
            "B_all_six": "Adds state, district, year and area for geography/time/scale specificity.",
            "C_crop_season_year_area": "Adds year and area but not geography.",
        },
        "prediction_time_availability": {
            "Crop": "Known when the farmer chooses a crop.",
            "Season": "Known from intended growing season.",
            "State/District": "Known at prediction time; district records do not identify a particular farm.",
            "YearStart": "Known for a planned prediction year.",
            "Area": "Planned area may be known; source records use observed area, so timing matters.",
            "Production": "Excluded because it leaks the target calculation.",
        },
        "decision_tree": tree_summary,
        "sugarcane": sugar_summary,
        "rolling_validation_winners": winners.to_dict(orient="records"),
    }
    (OUT / "review_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("Validation comparison; final test not used:")
    print(comparison.to_string(index=False))
    print("\nRolling validation winners:")
    print(winners.to_string(index=False))
    print("\nDecision Tree train/validation and Sugarcane check:")
    print(json.dumps({
        "tree_depth": tree_summary["tree_depth"],
        "tree_nodes": tree_summary["tree_nodes"],
        "tree_leaves": tree_summary["tree_leaves"],
        "train_metrics": tree_summary["train_metrics"],
        "validation_metrics": tree_summary["validation_metrics"],
        "sugarcane_mae_t_ha": sugar_summary["sugarcane_mae_t_ha"],
        "other_crop_mae_t_ha": sugar_summary["other_crop_mae_t_ha"],
    }, indent=2))
    return comparison, winners


if __name__ == "__main__":
    run_review()
