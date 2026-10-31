"""Produce residual data and summaries for the validation-selected model."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train_compare_models import build_candidate, candidates


def run_error_analysis():
    """Fit only through 2014 and examine the final 2015–2019 chronological holdout."""
    data = prepare()
    train = data["YearStart"] < 2015
    test = ~train
    comparison = pd.read_csv(MODULE / "evaluation/model_comparison.csv")
    selected = str(comparison.sort_values("validation_mae_t_ha").iloc[0]["model"])
    selection = json.loads((MODULE / "evaluation/model_selection.json").read_text())
    features = selection.get("selected_features", FEATURES)
    model = build_candidate(candidates()[selected], features=features).fit(data.loc[train, features], data.loc[train, TARGET])
    report = data.loc[test, ["State", "District", "Crop", "Season", "YearStart", TARGET]].copy()
    report["predicted_yield_t_ha"] = model.predict(data.loc[test, features])
    report["residual_t_ha"] = report[TARGET] - report["predicted_yield_t_ha"]
    report["absolute_error_t_ha"] = report["residual_t_ha"].abs()
    out = MODULE / "evaluation"
    report.to_csv(out / "test_predictions.csv", index=False)
    report.groupby("Crop").agg(
        records=(TARGET, "size"), mae_t_ha=("absolute_error_t_ha", "mean"),
        mean_residual_t_ha=("residual_t_ha", "mean")
    ).sort_values("records", ascending=False).to_csv(out / "error_by_crop.csv")
    report.groupby("State").agg(
        records=(TARGET, "size"), mae_t_ha=("absolute_error_t_ha", "mean"),
        mean_residual_t_ha=("residual_t_ha", "mean")
    ).to_csv(out / "error_by_state.csv")
    report.groupby("YearStart").agg(
        records=(TARGET, "size"), mae_t_ha=("absolute_error_t_ha", "mean"),
        mean_residual_t_ha=("residual_t_ha", "mean")
    ).to_csv(out / "error_by_year.csv")
    metrics = {
        "selected_by_validation": selected,
        "test_rows": int(len(report)),
        "mae_t_ha": float(mean_absolute_error(report[TARGET], report["predicted_yield_t_ha"])),
        "rmse_t_ha": float(np.sqrt(mean_squared_error(report[TARGET], report["predicted_yield_t_ha"]))),
        "r2": float(r2_score(report[TARGET], report["predicted_yield_t_ha"])),
        "median_residual_t_ha": float(report["residual_t_ha"].median()),
        "p95_absolute_error_t_ha": float(report["absolute_error_t_ha"].quantile(.95)),
        "largest_errors": report.nlargest(20, "absolute_error_t_ha").to_dict(orient="records"),
    }
    (out / "error_summary.json").write_text(json.dumps(metrics, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(report["predicted_yield_t_ha"], report["residual_t_ha"], alpha=.35)
    ax.axhline(0, color="red", linestyle="--")
    ax.set(title=f"Test residuals: {selected}", xlabel="Predicted yield (tonnes/hectare)", ylabel="Actual minus predicted (tonnes/hectare)")
    fig.tight_layout()
    fig.savefig(MODULE / "evaluation/residuals.png", dpi=160)
    plt.close(fig)
    print(json.dumps({k: v for k, v in metrics.items() if k != "largest_errors"}, indent=2))
    return metrics


if __name__ == "__main__":
    run_error_analysis()
