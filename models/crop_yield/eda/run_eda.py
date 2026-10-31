"""Create a reproducible, read-only exploratory analysis of the raw yield source."""
from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW = ROOT / "DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv"
OUT = MODULE / "eda/plots"
REPORTS = MODULE / "reports/current"


def run_eda():
    """Summarize raw observations and save labelled plots without changing source data."""
    data = pd.read_csv(RAW)
    data["YearStart"] = pd.to_numeric(data["Year"].astype(str).str[:4], errors="coerce")
    for name in ["Area", "Production", "Yield"]:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # Write a concise profile and summaries so the charts are backed by numbers.
    profile = pd.DataFrame({
        "column": data.columns,
        "dtype": [str(data[c].dtype) for c in data.columns],
        "missing_count": [int(data[c].isna().sum()) for c in data.columns],
        "missing_percent": [float(data[c].isna().mean() * 100) for c in data.columns],
        "unique_values": [int(data[c].nunique(dropna=True)) for c in data.columns],
    })
    profile.to_csv(REPORTS / "eda_column_profile.csv", index=False)
    data.describe(include="all").transpose().to_csv(REPORTS / "eda_descriptive_summary.csv")
    data.groupby("Crop", dropna=False)["Yield"].agg(["count", "mean", "median", "std"]).sort_values(
        "count", ascending=False
    ).to_csv(REPORTS / "eda_crop_yield_summary.csv")
    data.groupby("State", dropna=False)["Yield"].agg(["count", "mean", "median", "std"]).to_csv(
        REPORTS / "eda_state_yield_summary.csv"
    )
    data.groupby("District", dropna=False)["Yield"].agg(["count", "mean", "median", "std"]).to_csv(
        REPORTS / "eda_district_yield_summary.csv"
    )
    data.groupby("Season", dropna=False)["Yield"].agg(["count", "mean", "median", "std"]).to_csv(
        REPORTS / "eda_season_yield_summary.csv"
    )
    data.groupby("YearStart")["Yield"].agg(["count", "mean", "median"]).to_csv(
        REPORTS / "eda_year_yield_summary.csv"
    )

    # Histograms and boxplots show skew and spread without automatically removing outliers.
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=data, x="Yield", bins=50, ax=ax)
    ax.set(title="Reported crop yield distribution", xlabel="Yield (tonnes per hectare)", ylabel="Records")
    fig.tight_layout(); fig.savefig(OUT / "yield_distribution.png", dpi=160); plt.close(fig)

    top_crops = data["Crop"].value_counts().head(12).index
    fig, ax = plt.subplots(figsize=(13, 6))
    sns.boxplot(data=data[data["Crop"].isin(top_crops)], x="Crop", y="Yield", ax=ax, showfliers=False)
    ax.tick_params(axis="x", rotation=45)
    ax.set(title="Yield spread for the 12 most frequently recorded crops", xlabel="Crop", ylabel="Yield (tonnes per hectare)")
    fig.tight_layout(); fig.savefig(OUT / "yield_by_crop_boxplot.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=data, x="State", y="Yield", ax=ax, showfliers=False)
    ax.set(title="Yield spread by state", xlabel="State", ylabel="Yield (tonnes per hectare)")
    fig.tight_layout(); fig.savefig(OUT / "yield_by_state_boxplot.png", dpi=160); plt.close(fig)

    # District spreads are descriptive; show all districts in a tall readable figure.
    fig, ax = plt.subplots(figsize=(15, 9))
    sns.boxplot(data=data, x="District", y="Yield", ax=ax, showfliers=False)
    ax.tick_params(axis="x", rotation=90)
    ax.set(title="Yield spread by district (outlier markers hidden for readability)", xlabel="District", ylabel="Yield (tonnes per hectare)")
    fig.tight_layout(); fig.savefig(OUT / "yield_by_district_boxplot.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=data, x="Season", y="Yield", ax=ax, showfliers=False)
    ax.set(title="Yield spread by season", xlabel="Season", ylabel="Yield (tonnes per hectare)")
    fig.tight_layout(); fig.savefig(OUT / "yield_by_season_boxplot.png", dpi=160); plt.close(fig)

    yearly = data.groupby("YearStart")["Yield"].median().dropna()
    fig, ax = plt.subplots(figsize=(10, 5))
    yearly.plot(marker="o", ax=ax)
    ax.set(title="Median reported yield by crop year", xlabel="Starting year", ylabel="Median yield (tonnes per hectare)")
    fig.tight_layout(); fig.savefig(OUT / "yield_trend_by_year.png", dpi=160); plt.close(fig)

    crop_mean = data.groupby("Crop")["Yield"].mean().sort_values().tail(15)
    fig, ax = plt.subplots(figsize=(10, 7))
    crop_mean.plot(kind="barh", ax=ax)
    ax.set(title="Mean yield for 15 highest-mean crops (descriptive)", xlabel="Mean yield (tonnes per hectare)", ylabel="Crop")
    fig.tight_layout(); fig.savefig(OUT / "mean_yield_by_crop.png", dpi=160); plt.close(fig)

    numerical = data[["Area", "Production", "Yield", "YearStart"]].corr(numeric_only=True)
    numerical.to_csv(REPORTS / "eda_numeric_correlations.csv")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(numerical, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax)
    ax.set(title="Correlation among recorded numerical fields")
    fig.tight_layout(); fig.savefig(OUT / "numeric_correlation_heatmap.png", dpi=160); plt.close(fig)

    missing = data.isna().sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 4))
    missing[missing.gt(0)].plot(kind="bar", ax=ax)
    ax.set(title="Missing values by column", xlabel="Column", ylabel="Missing rows")
    fig.tight_layout(); fig.savefig(OUT / "missing_values.png", dpi=160); plt.close(fig)

    # IQR fences identify records for human review; they do not filter training data.
    q1, q3 = data["Yield"].quantile([0.25, 0.75])
    fence_low, fence_high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    outliers = data.loc[data["Yield"].lt(fence_low) | data["Yield"].gt(fence_high)].copy()
    outliers.to_csv(REPORTS / "eda_yield_iqr_review.csv", index=False)
    print(f"EDA saved {len(list(OUT.glob('*.png')))} plots; {len(outliers)} IQR-flagged yields saved for review.")
    return data


if __name__ == "__main__":
    run_eda()
