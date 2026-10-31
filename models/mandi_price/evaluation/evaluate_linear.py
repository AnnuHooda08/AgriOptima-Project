"""Chronologically evaluate Linear Regression against simple price baselines."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_linear_data import load_model_data  # noqa: E402
from train_linear import FEATURES, build_pipeline  # noqa: E402


REPORT_DIR = MODULE / "evaluation" / "reports" / "linear_regression"
TRAIN_END = pd.Timestamp("2020-01-01")
VALIDATION_END = pd.Timestamp("2023-01-01")
TEST_START = pd.Timestamp("2023-01-01")


def _metric_row(actual: pd.Series, predicted: np.ndarray, name: str) -> dict:
    """Return price errors in rupees per quintal plus R-squared."""
    return {
        "model": name,
        "records": int(len(actual)),
        "mae_rs_per_quintal": float(mean_absolute_error(actual, predicted)),
        "rmse_rs_per_quintal": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def evaluate() -> dict:
    """Use validation for review and hold 2023+ out for a single final check."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_model_data().sort_values("date").reset_index(drop=True)
    training = data["date"] < TRAIN_END
    validation = (data["date"] >= TRAIN_END) & (data["date"] < VALIDATION_END)
    test = data["date"] >= TEST_START
    if not training.any() or not validation.any() or not test.any():
        raise ValueError("The chronological train, validation, and test periods must all contain data.")

    # First fit sees only pre-2020 observations; it provides the validation score.
    validation_model = build_pipeline().fit(data.loc[training, FEATURES], data.loc[training, "price"])
    validation_frame = data.loc[validation].copy()
    validation_prediction = validation_model.predict(validation_frame[FEATURES])
    validation_metrics = [
        _metric_row(validation_frame["price"], validation_frame["lag_1"].to_numpy(), "previous_month_persistence"),
        _metric_row(validation_frame["price"], validation_frame["lag_12"].to_numpy(), "same_month_previous_year"),
        _metric_row(validation_frame["price"], validation_prediction, "linear_regression"),
    ]

    # Once the model is fixed, refit on train + validation; keep 2023+ out of fit.
    pre_test = data["date"] < TEST_START
    final_model = build_pipeline().fit(data.loc[pre_test, FEATURES], data.loc[pre_test, "price"])
    test_frame = data.loc[test].copy()
    test_prediction = final_model.predict(test_frame[FEATURES])
    test_metrics = [
        _metric_row(test_frame["price"], test_frame["lag_1"].to_numpy(), "previous_month_persistence"),
        _metric_row(test_frame["price"], test_frame["lag_12"].to_numpy(), "same_month_previous_year"),
        _metric_row(test_frame["price"], test_prediction, "linear_regression"),
    ]

    predictions = test_frame[["date", "price", "lag_1", "lag_12"]].rename(columns={"price": "actual_price"})
    predictions["linear_regression_prediction"] = test_prediction
    predictions["persistence_prediction"] = test_frame["lag_1"].to_numpy()
    predictions["seasonal_baseline_prediction"] = test_frame["lag_12"].to_numpy()
    predictions["residual_actual_minus_predicted"] = predictions["actual_price"] - predictions["linear_regression_prediction"]
    predictions["absolute_error"] = predictions["residual_actual_minus_predicted"].abs()
    predictions.to_csv(REPORT_DIR / "test_predictions.csv", index=False)

    # Store row-level errors as a transparent price-error analysis table.
    error_summary = predictions.assign(year=predictions["date"].dt.year).groupby("year").agg(
        records=("absolute_error", "size"), mean_absolute_error=("absolute_error", "mean"),
        largest_absolute_error=("absolute_error", "max"), mean_signed_error=("residual_actual_minus_predicted", "mean"),
    ).reset_index()
    error_summary.to_csv(REPORT_DIR / "test_error_by_year.csv", index=False)

    metrics = {
        "target": "national monthly median maize modal price, Rs/quintal",
        "features": FEATURES,
        "feature_reasoning": {
            "lag_1_lag_2_lag_3_lag_12": "Previous observed national monthly prices; available for a rolling one-month-ahead forecast.",
            "month": "Calendar seasonality; treated as a category with one-hot encoding.",
            "year": "A simple long-term time trend; extrapolation beyond the observed period is uncertain.",
            "excluded_fields": "State, district, market and commodity are not inputs because the modeled target is a national maize aggregate. Arrivals and same-month min/max prices are contemporaneous with the target and could leak information.",
        },
        "split": {
            "training_before": str(TRAIN_END.date()),
            "training_rows": int(training.sum()),
            "validation_from": str(TRAIN_END.date()),
            "validation_before": str(VALIDATION_END.date()),
            "validation_rows": int(validation.sum()),
            "final_fit_before_test": str(TEST_START.date()),
            "final_fit_rows": int(pre_test.sum()),
            "test_from": str(TEST_START.date()),
            "test_rows": int(test.sum()),
            "test_first_month": str(test_frame["date"].min().date()),
            "test_last_month": str(test_frame["date"].max().date()),
            "test_not_used_for_preprocessing_or_fit": True,
            "test_protocol": "Rolling one-month-ahead; the previous actual month is available before the next month's prediction.",
        },
        "validation_metrics": validation_metrics,
        "final_test_metrics": test_metrics,
        "interpretation": "Compare MAE/RMSE/R2 with the baselines; a larger MAE or RMSE than persistence means the learned model is worse for this evaluation.",
    }
    (REPORT_DIR / "linear_regression_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    pd.DataFrame(validation_metrics).assign(split="validation").to_csv(REPORT_DIR / "validation_metrics.csv", index=False)
    pd.DataFrame(test_metrics).assign(split="final_test").to_csv(REPORT_DIR / "final_test_metrics.csv", index=False)

    # Plot actual and model/baseline predictions over the untouched final period.
    plt.figure(figsize=(10, 5))
    plt.plot(test_frame["date"], test_frame["price"], marker="o", label="Actual")
    plt.plot(test_frame["date"], test_prediction, marker="o", label="Linear Regression")
    plt.plot(test_frame["date"], test_frame["lag_1"], linestyle="--", label="Previous-month baseline")
    plt.xlabel("Month")
    plt.ylabel("Modal price (Rs/quintal)")
    plt.title("Actual and predicted national maize prices: 2023 onward")
    plt.legend()
    plt.grid(alpha=.25)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "actual_vs_predicted.png", dpi=160)
    plt.close()

    # A residual near zero is a close prediction; systematic patterns indicate bias.
    plt.figure(figsize=(8, 5))
    plt.scatter(test_prediction, predictions["residual_actual_minus_predicted"], color="#e07a5f", alpha=.8)
    plt.axhline(0, color="black", linewidth=1)
    plt.xlabel("Predicted price (Rs/quintal)")
    plt.ylabel("Residual: actual minus predicted (Rs/quintal)")
    plt.title("Linear Regression residuals on final test months")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "residuals.png", dpi=160)
    plt.close()

    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    evaluate()
