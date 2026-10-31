"""Build a safe monthly maize price series for the Linear Regression model."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_FILE = ROOT / "DataSets" / "india_mandi_prices_2000_2024" / "Maize.csv"
PROCESSED_DIR = MODULE / "data" / "processed" / "linear_regression"
MODEL_DATA = PROCESSED_DIR / "maize_monthly.csv"
REJECTED_DATA = PROCESSED_DIR / "rejected_market_rows.csv"
SUMMARY_FILE = PROCESSED_DIR / "preprocessing_summary.json"


def load_model_data(force_prepare: bool = False) -> pd.DataFrame:
    """Load the derived monthly rows, preparing them when they do not exist."""
    if force_prepare or not MODEL_DATA.exists():
        return prepare_data()
    data = pd.read_csv(MODEL_DATA, parse_dates=["date"])
    return data


def prepare_data() -> pd.DataFrame:
    """Clean raw prices, log rejected rows, and derive actual-calendar-month lags."""
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Maize market dataset not found: {RAW_FILE}")

    raw = pd.read_csv(RAW_FILE, low_memory=False)
    original_rows = len(raw)
    exact_duplicate = raw.duplicated(keep="first")
    # Keep the first copy of a byte-for-byte duplicate and record every removed
    # extra copy so it is visible instead of silently affecting monthly medians.
    duplicate_rows = raw.loc[exact_duplicate].copy()
    duplicate_rows["exclusion_reason"] = "exact_duplicate_source_row"
    unique = raw.loc[~exact_duplicate].copy()

    dates = pd.to_datetime(unique["Reported Date"].astype("string").str.strip(), errors="coerce", dayfirst=True)
    prices = pd.to_numeric(unique["Modal Price (Rs./Quintal)"], errors="coerce")
    reasons = pd.Series("", index=unique.index, dtype="string")
    reasons.loc[dates.isna()] = "invalid_or_missing_reported_date"
    reasons.loc[prices.isna()] = reasons.loc[prices.isna()].map(
        lambda old: f"{old}; invalid_or_missing_modal_price" if old else "invalid_or_missing_modal_price"
    )
    nonpositive = prices.notna() & prices.le(0)
    reasons.loc[nonpositive] = reasons.loc[nonpositive].map(
        lambda old: f"{old}; nonpositive_modal_price" if old else "nonpositive_modal_price"
    )
    valid = reasons.eq("")
    rejected_source = unique.loc[~valid].copy()
    rejected_source["exclusion_reason"] = reasons.loc[~valid]
    rejected = pd.concat([duplicate_rows, rejected_source], ignore_index=True, sort=False)

    accepted = pd.DataFrame({"date": dates.loc[valid], "price": prices.loc[valid]})
    # A monthly median summarizes observed market-level modal prices. The
    # calendar index leaves truly unreported months missing rather than faking data.
    monthly = accepted.set_index("date")["price"].resample("MS").median().asfreq("MS")
    features = monthly.rename("price").to_frame()
    for lag in (1, 2, 3, 12):
        # shift() here means an exact prior calendar month because every month
        # is present in the index, even when its actual price value is missing.
        features[f"lag_{lag}"] = features["price"].shift(lag)
    features["month"] = features.index.month
    features["year"] = features.index.year
    feature_columns = ["lag_1", "lag_2", "lag_3", "lag_12", "month", "year"]
    model_data = features.dropna(subset=["price", *feature_columns]).reset_index(names="date")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    model_data.to_csv(MODEL_DATA, index=False)
    rejected.to_csv(REJECTED_DATA, index=False)
    summary = {
        "source_file": str(RAW_FILE.relative_to(ROOT)),
        "raw_records": int(original_rows),
        "exact_duplicate_rows_logged_and_excluded": int(exact_duplicate.sum()),
        "invalid_or_missing_date_rows": int(dates.isna().sum()),
        "missing_or_non_numeric_modal_price_rows": int(prices.isna().sum()),
        "nonpositive_modal_price_rows": int(nonpositive.sum()),
        "rejected_rows_written": int(len(rejected)),
        "accepted_daily_market_rows": int(len(accepted)),
        "observed_months": int(monthly.notna().sum()),
        "calendar_months_in_range": int(len(monthly)),
        "missing_calendar_months_not_filled": int(monthly.isna().sum()),
        "model_rows_after_calendar_lags": int(len(model_data)),
        "model_first_month": str(model_data["date"].min().date()),
        "model_last_month": str(model_data["date"].max().date()),
        "target": "monthly median of market modal prices, Rs per quintal",
        "feature_columns": feature_columns,
        "future_arrivals_or_same_month_minimum_maximum_prices_used": False,
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Linear price preprocessing: {len(model_data)} monthly rows; logged {len(rejected)} rejected rows.")
    return model_data


if __name__ == "__main__":
    prepare_data()
