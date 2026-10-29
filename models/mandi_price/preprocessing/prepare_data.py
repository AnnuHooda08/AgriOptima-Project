"""Clean maize prices and create lags that respect actual calendar months."""
from pathlib import Path
import json
import pandas as pd

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_FILE = ROOT / "DataSets" / "india_mandi_prices_2000_2024" / "Maize.csv"
OUTPUT = MODULE / "data" / "processed" / "maize_monthly.csv"
REJECTED = MODULE / "data" / "processed" / "rejected_market_rows.csv"
SUMMARY = MODULE / "evaluation" / "preprocessing_summary.json"

def prepare():
    # Only load the fields used by the national monthly price benchmark.
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Maize market dataset not found: {RAW_FILE}")
    data = pd.read_csv(RAW_FILE, usecols=["Reported Date", "Modal Price (Rs./Quintal)"])
    source_rows = len(data)
    dates = pd.to_datetime(data["Reported Date"].astype("string").str.strip(), errors="coerce")
    prices = pd.to_numeric(data["Modal Price (Rs./Quintal)"], errors="coerce")

    # Preserve invalid source entries in a small audit table with their specific issue.
    reasons = pd.Series("", index=data.index, dtype="string")
    bad_date = dates.isna()
    bad_price = prices.isna()
    nonpositive = prices.notna() & prices.le(0)
    reasons.loc[bad_date] = "invalid_or_missing_reported_date"
    reasons.loc[bad_price] = reasons.loc[bad_price].apply(
        lambda old: f"{old}; invalid_or_missing_modal_price" if old else "invalid_or_missing_modal_price"
    )
    reasons.loc[nonpositive] = reasons.loc[nonpositive].apply(
        lambda old: f"{old}; nonpositive_modal_price" if old else "nonpositive_modal_price"
    )
    valid = reasons.eq("")
    rejected = data.loc[~valid].copy()
    rejected["exclusion_reason"] = reasons.loc[~valid]
    clean = pd.DataFrame({"date": dates.loc[valid], "price": prices.loc[valid]})

    # Monthly median handles many market-level rows; missing calendar months stay missing.
    monthly = clean.set_index("date")["price"].resample("MS").median().asfreq("MS")
    features = monthly.rename("price").to_frame()
    for months in [1, 2, 3, 12]:
        # A shift means exactly that many calendar months, never the previous available row.
        features[f"lag_{months}"] = features["price"].shift(months)
    features["month"] = features.index.month
    features["year"] = features.index.year
    columns = ["lag_1", "lag_2", "lag_3", "lag_12", "month", "year"]
    model_data = features.dropna(subset=["price"] + columns).reset_index(names="date")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    model_data.to_csv(OUTPUT, index=False)
    rejected.to_csv(REJECTED, index=False)
    summary = {
        "source_file": str(RAW_FILE.relative_to(ROOT)),
        "source_rows": int(source_rows),
        "valid_price_records": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "observed_months": int(monthly.notna().sum()),
        "calendar_months": int(len(monthly)),
        "model_rows_after_calendar_lags": int(len(model_data)),
        "date_min": str(model_data["date"].min().date()),
        "date_max": str(model_data["date"].max().date()),
        "aggregation": "monthly median modal price, Rs/quintal",
        "missing_months_are_not_filled": True,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Mandi preprocessing: {len(model_data)} model months; rejected {len(rejected)} of {source_rows} raw records.")
    return model_data

if __name__ == "__main__":
    prepare()
