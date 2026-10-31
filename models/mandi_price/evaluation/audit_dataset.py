"""Audit the local AGMARKNET commodity files and maize modeling data.

The collection inventory is streamed one file at a time so the 3 GB raw
directory is never loaded into memory all at once. Raw files are read-only.
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT.parent.parent / "DataSets" / "india_mandi_prices_2000_2024"
OUTPUT_DIR = ROOT / "evaluation" / "reports" / "linear_regression"
CHUNK_ROWS = 150_000


def _pick(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    """Choose the first recognized name from a CSV header."""
    return next((candidate for candidate in candidates if candidate in columns), None)


def _inventory_one_file(path: Path) -> dict:
    """Stream one commodity file and summarize its reported modal prices."""
    result = {
        "filename": path.name,
        "commodity_label": path.stem,
        "file_size_bytes": path.stat().st_size,
        "status": "available",
        "records": 0,
        "price_column": "",
        "price_unit_from_header": "unknown",
        "date_min": "",
        "date_max": "",
        "states": 0,
        "markets": 0,
        "missing_modal_price": 0,
        "nonpositive_modal_price": 0,
        "modal_min": np.nan,
        "modal_max": np.nan,
        "modal_mean": np.nan,
        "modal_median": np.nan,
        "exact_duplicate_rows": "not_checked_for_every_file",
    }

    # Git LFS pointer files and empty placeholders are present in the folder,
    # but they do not contain market observations to analyze.
    with path.open("rb") as handle:
        first = handle.readline().decode("utf-8", errors="replace").strip()
    if first.startswith("version https://git-lfs.github.com/spec/v1"):
        result["status"] = "git_lfs_pointer_data_not_present"
        return result
    if path.stat().st_size <= 1:
        result["status"] = "empty_placeholder"
        return result

    header = pd.read_csv(path, nrows=0)
    columns = header.columns.tolist()
    price_col = _pick(columns, ("Modal Price (Rs./Quintal)", "Modal Price"))
    date_col = _pick(columns, ("Reported Date", "Price Date", "Date"))
    state_col = _pick(columns, ("State Name", "State"))
    market_col = _pick(columns, ("Market Name", "Market"))
    result["columns"] = columns
    result["price_column"] = price_col or ""
    if price_col and "Rs./Quintal" in price_col:
        result["price_unit_from_header"] = "Rs/quintal"
    elif price_col:
        result["price_unit_from_header"] = "unit not stated in column name"
    else:
        result["status"] = "modal_price_column_not_found"
        return result

    selected = [column for column in (price_col, date_col, state_col, market_col) if column]
    prices: list[np.ndarray] = []
    states: set[str] = set()
    markets: set[str] = set()
    first_date = None
    last_date = None
    for chunk in pd.read_csv(path, usecols=selected, chunksize=CHUNK_ROWS, low_memory=False):
        result["records"] += len(chunk)
        values = pd.to_numeric(chunk[price_col], errors="coerce")
        result["missing_modal_price"] += int(values.isna().sum())
        result["nonpositive_modal_price"] += int(values.notna().mul(values.le(0)).sum())
        valid = values[values.gt(0)].dropna().to_numpy(dtype=float)
        if len(valid):
            prices.append(valid)
        if date_col:
            dates = pd.to_datetime(chunk[date_col], errors="coerce", format="mixed", dayfirst=True).dropna()
            if len(dates):
                chunk_min, chunk_max = dates.min(), dates.max()
                first_date = chunk_min if first_date is None else min(first_date, chunk_min)
                last_date = chunk_max if last_date is None else max(last_date, chunk_max)
        if state_col:
            states.update(chunk[state_col].dropna().astype(str).str.strip().unique())
        if market_col:
            markets.update(chunk[market_col].dropna().astype(str).str.strip().unique())

    if prices:
        values = np.concatenate(prices)
        result["modal_min"] = float(values.min())
        result["modal_max"] = float(values.max())
        result["modal_mean"] = float(values.mean())
        result["modal_median"] = float(np.median(values))
    result["states"] = len(states)
    result["markets"] = len(markets)
    if first_date is not None:
        result["date_min"] = str(first_date.date())
        result["date_max"] = str(last_date.date())
    return result


def _audit_maize() -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Summarize raw maize observations, duplicates, prices, and relationships."""
    path = RAW_DIR / "Maize.csv"
    data = pd.read_csv(path, low_memory=False)
    prices = pd.to_numeric(data["Modal Price (Rs./Quintal)"], errors="coerce")
    dates = pd.to_datetime(data["Reported Date"].astype("string").str.strip(), errors="coerce", format="mixed", dayfirst=True)
    valid_prices = prices[prices.notna() & prices.gt(0)]
    price_distributions = {}
    for column in ("Min Price (Rs./Quintal)", "Max Price (Rs./Quintal)", "Modal Price (Rs./Quintal)"):
        values = pd.to_numeric(data[column], errors="coerce")
        positive = values[values.gt(0)].dropna()
        price_distributions[column] = {
            "missing_or_non_numeric": int(values.isna().sum()),
            "nonpositive": int((values.notna() & values.le(0)).sum()),
            "positive_count": int(positive.count()),
            "positive_min": float(positive.min()),
            "positive_max": float(positive.max()),
            "positive_mean": float(positive.mean()),
            "positive_median": float(positive.median()),
        }
    market_medians = data.assign(_price=prices, _date=dates).dropna(subset=["_price"])
    market_medians = market_medians.loc[market_medians["_price"].gt(0)].groupby("Market Name").agg(
        observations=("_price", "size"), median_modal_price=("_price", "median"),
        state=("State Name", "first"),
    ).reset_index().sort_values("observations", ascending=False)
    year_month = pd.DataFrame({"date": dates, "price": prices})
    year_month = year_month.loc[year_month["price"].gt(0)].set_index("date")["price"].resample("MS").median()

    lower, upper = valid_prices.quantile([.25, .75])
    iqr = upper - lower
    iqr_flag = (prices < lower - 1.5 * iqr) | (prices > upper + 1.5 * iqr)
    outliers = data.loc[iqr_flag].copy()
    outliers.insert(0, "source_csv_row", outliers.index + 2)
    outliers["review_reason"] = "Modal price falls beyond the overall maize IQR fences; review only, not treated as an error"
    range_min = pd.to_numeric(data["Min Price (Rs./Quintal)"], errors="coerce")
    range_max = pd.to_numeric(data["Max Price (Rs./Quintal)"], errors="coerce")
    range_violation = (range_min > prices) | (prices > range_max)
    range_issues = data.loc[range_violation].copy()
    range_issues.insert(0, "source_csv_row", range_issues.index + 2)
    range_issues["review_reason"] = "Reported minimum/modal/maximum prices are not ordered; source values retained"
    summary = {
        "source_filename": path.name,
        "rows": int(len(data)),
        "columns": data.columns.tolist(),
        "missing_values_by_column": data.isna().sum().astype(int).to_dict(),
        "date_min": str(dates.min().date()),
        "date_max": str(dates.max().date()),
        "invalid_dates": int(dates.isna().sum()),
        "states": int(data["State Name"].nunique()),
        "districts": int(data["District Name"].nunique()),
        "markets": int(data["Market Name"].nunique()),
        "varieties": int(data["Variety"].nunique()),
        "groups": int(data["Group"].nunique()),
        "price_unit": "Rs per quintal as declared by column names",
        "arrivals_unit": "Tonnes as declared by column name",
        "modal_price_nonpositive": int((prices.notna() & prices.le(0)).sum()),
        "exact_duplicate_rows": int(data.duplicated().sum()),
        "duplicate_market_variety_date_rows": int(data.duplicated(
            ["State Name", "District Name", "Market Name", "Variety", "Reported Date"], keep=False
        ).sum()),
        "duplicate_market_variety_date_extra_rows": int(data.duplicated(
            ["State Name", "District Name", "Market Name", "Variety", "Reported Date"]
        ).sum()),
        "modal_price_valid_distribution": {
            "count": int(valid_prices.count()), "min": float(valid_prices.min()),
            "max": float(valid_prices.max()), "mean": float(valid_prices.mean()),
            "median": float(valid_prices.median()), "std": float(valid_prices.std()),
            "p01": float(valid_prices.quantile(.01)), "p25": float(lower),
            "p75": float(upper), "p99": float(valid_prices.quantile(.99)),
            "iqr_outside_count": int(((valid_prices < lower - 1.5 * iqr) | (valid_prices > upper + 1.5 * iqr)).sum()),
        },
        "minimum_price_invalid_count": int(pd.to_numeric(data["Min Price (Rs./Quintal)"], errors="coerce").isna().sum()),
        "maximum_price_invalid_count": int(pd.to_numeric(data["Max Price (Rs./Quintal)"], errors="coerce").isna().sum()),
        "modal_price_invalid_count": int(prices.isna().sum()),
        "price_column_distributions_positive_values": price_distributions,
        "min_modal_max_order_violations": int(range_violation.sum()),
        "monthly_median_range": {
            "first_observed_month": str(year_month.dropna().index.min().date()),
            "last_observed_month": str(year_month.dropna().index.max().date()),
            "observed_months": int(year_month.notna().sum()),
            "missing_calendar_months": int(year_month.isna().sum()),
        },
    }
    return summary, market_medians, outliers, range_issues


def main() -> None:
    """Write collection inventory, detailed maize audit, and readable EDA plots."""
    parser = argparse.ArgumentParser(description="Audit the mandi CSV collection and maize prices.")
    parser.add_argument(
        "--maize-only",
        action="store_true",
        help="Reuse the existing collection inventory and refresh the maize-only audit outputs.",
    )
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory_path = OUTPUT_DIR / "commodity_file_inventory.csv"
    if args.maize_only and inventory_path.exists():
        inventory_df = pd.read_csv(inventory_path)
    else:
        inventory = [_inventory_one_file(path) for path in sorted(RAW_DIR.glob("*.csv"), key=lambda item: item.name.casefold())]
        inventory_df = pd.DataFrame(inventory)
        inventory_df.to_csv(inventory_path, index=False)
    maize, mandi_summary, outliers, range_issues = _audit_maize()
    (OUTPUT_DIR / "maize_dataset_audit.json").write_text(json.dumps(maize, indent=2) + "\n")
    mandi_summary.to_csv(OUTPUT_DIR / "maize_mandi_price_summary.csv", index=False)
    outliers.to_csv(OUTPUT_DIR / "maize_price_outlier_review.csv", index=False)
    range_issues.to_csv(OUTPUT_DIR / "maize_price_range_issues.csv", index=False)
    maize_audit_columns = pd.read_csv(
        RAW_DIR / "Maize.csv",
        usecols=["Modal Price (Rs./Quintal)", "Reported Date"],
    )
    audit_dates = pd.to_datetime(maize_audit_columns["Reported Date"], errors="coerce", format="mixed", dayfirst=True)
    audit_prices = pd.to_numeric(maize_audit_columns["Modal Price (Rs./Quintal)"], errors="coerce")
    annual_data = pd.DataFrame({"year": audit_dates.dt.year, "price": audit_prices})
    annual_data = annual_data.loc[annual_data["price"].gt(0)].groupby("year")["price"].agg(
        records="count", mean="mean", median="median", minimum="min", maximum="max"
    ).reset_index()
    annual_data.to_csv(OUTPUT_DIR / "maize_yearly_price_summary.csv", index=False)

    # Plot only data whose unit is explicitly present in its CSV column header.
    comparable = inventory_df[
        inventory_df["status"].eq("available")
        & inventory_df["price_unit_from_header"].eq("Rs/quintal")
        & inventory_df["modal_median"].notna()
    ].nlargest(15, "records").sort_values("modal_median")
    plt.figure(figsize=(10, 7))
    plt.barh(comparable["commodity_label"], comparable["modal_median"], color="#3f7f5f")
    plt.xlabel("Median reported modal price (Rs/quintal)")
    plt.ylabel("Commodity file")
    plt.title("Median modal prices in the 15 largest unit-labeled commodity files")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "commodity_price_comparison.png", dpi=160)
    plt.close()

    maize_file = RAW_DIR / "Maize.csv"
    maize_data = pd.read_csv(maize_file, usecols=["Modal Price (Rs./Quintal)", "Reported Date"])
    modal = pd.to_numeric(maize_data["Modal Price (Rs./Quintal)"], errors="coerce")
    modal = modal[modal.gt(0)].dropna()
    display_limit = float(modal.quantile(.99))
    plt.figure(figsize=(9, 5))
    plt.hist(modal[modal <= display_limit], bins=70, color="#277da1", edgecolor="white")
    plt.xlabel(f"Reported modal price (Rs/quintal; plot limited to p99 = {display_limit:.0f})")
    plt.ylabel("Market-day rows")
    plt.title("Maize modal-price distribution (positive prices; upper 1% omitted from plot view)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "maize_price_distribution.png", dpi=160)
    plt.close()

    dates = pd.to_datetime(maize_data["Reported Date"], errors="coerce", format="mixed", dayfirst=True)
    monthly = pd.DataFrame({"date": dates, "price": pd.to_numeric(maize_data["Modal Price (Rs./Quintal)"], errors="coerce")})
    monthly = monthly.loc[monthly["price"].gt(0)].set_index("date")["price"].resample("MS").median()
    monthly_features = monthly.rename("price").to_frame()
    for lag in (1, 2, 3, 12):
        monthly_features[f"lag_{lag}"] = monthly_features["price"].shift(lag)
    monthly_features["year"] = monthly_features.index.year
    monthly_features["month"] = monthly_features.index.month
    monthly_features.corr(numeric_only=True).to_csv(OUTPUT_DIR / "maize_monthly_numeric_correlations.csv")
    plt.figure(figsize=(11, 5))
    plt.plot(monthly.index, monthly.values, color="#277da1", linewidth=1.5)
    plt.xlabel("Month")
    plt.ylabel("Median modal price (Rs/quintal)")
    plt.title("National maize monthly median modal-price series")
    plt.grid(alpha=.25)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "maize_monthly_price_trend.png", dpi=160)
    plt.close()

    top_markets = mandi_summary.head(15).sort_values("median_modal_price")
    plt.figure(figsize=(10, 7))
    plt.barh(top_markets["Market Name"], top_markets["median_modal_price"], color="#e07a5f")
    plt.xlabel("Median modal price (Rs/quintal)")
    plt.ylabel("Market")
    plt.title("Maize mandi price variation (15 markets with most observations)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "maize_mandi_price_variation.png", dpi=160)
    plt.close()

    counts = inventory_df["status"].value_counts().to_dict()
    collection = {
        "folder": str(RAW_DIR.relative_to(ROOT.parent.parent)),
        "csv_entries": int(len(inventory_df)),
        "statuses": counts,
        "total_bytes": int(inventory_df["file_size_bytes"].sum()),
        "commodity_labels": int(inventory_df["commodity_label"].nunique()),
        "available_records": int(inventory_df.loc[inventory_df["status"].eq("available"), "records"].sum()),
        "price_units_declared_in_header": inventory_df.loc[inventory_df["status"].eq("available"), "price_unit_from_header"].value_counts().to_dict(),
        "notes": [
            "Each commodity is stored in a separate CSV; the folder is not a single homogeneous table.",
            "Git LFS pointers do not contain the referenced data in this checkout.",
            "Ten one-byte placeholders contain no CSV header or observations.",
            "The maize model uses its own explicit Rs./Quintal columns; rows from other commodities are not combined into its target.",
        ],
    }
    (OUTPUT_DIR / "collection_summary.json").write_text(json.dumps(collection, indent=2) + "\n")
    print(json.dumps({"collection": collection, "maize": maize}, indent=2))


if __name__ == "__main__":
    main()
