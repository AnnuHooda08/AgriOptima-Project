
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "crop_yield_cleaned.csv"
)

REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

required = [
    "State", "District", "Crop", "Season",
    "YearStart", "Area", "Production", "Yield"
]

missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# Calculate outlier thresholds separately for each crop.
crop_stats = (
    df.groupby("Crop")["Yield"]
    .agg(
        Q1=lambda x: x.quantile(0.25),
        Q3=lambda x: x.quantile(0.75),
        Records="count"
    )
    .reset_index()
)

crop_stats["IQR"] = crop_stats["Q3"] - crop_stats["Q1"]
crop_stats["Lower_Bound"] = (
    crop_stats["Q1"] - 1.5 * crop_stats["IQR"]
).clip(lower=0)
crop_stats["Upper_Bound"] = (
    crop_stats["Q3"] + 1.5 * crop_stats["IQR"]
)

df = df.merge(
    crop_stats[
        ["Crop", "Q1", "Q3", "IQR",
         "Lower_Bound", "Upper_Bound"]
    ],
    on="Crop",
    how="left"
)

df["Outlier_Flag"] = (
    (df["Yield"] < df["Lower_Bound"])
    | (df["Yield"] > df["Upper_Bound"])
)

# Flag the most extreme records for manual review.
outliers = df[df["Outlier_Flag"]].copy()
outliers["Distance_Above_Bound"] = (
    outliers["Yield"] - outliers["Upper_Bound"]
).clip(lower=0)

outliers = outliers.sort_values(
    "Distance_Above_Bound",
    ascending=False
)

columns = [
    "State", "District", "Crop", "Season",
    "YearStart", "Area", "Production", "Yield",
    "Q1", "Q3", "Upper_Bound",
    "Distance_Above_Bound"
]

outliers[columns].to_csv(
    REPORT_DIR / "crop_outlier_audit.csv",
    index=False
)

summary = (
    outliers.groupby("Crop")
    .agg(
        Flagged_Records=("Yield", "size"),
        Maximum_Yield=("Yield", "max"),
        Median_Yield=("Yield", "median")
    )
    .sort_values("Flagged_Records", ascending=False)
)

summary.to_csv(
    REPORT_DIR / "crop_outlier_summary.csv"
)

print("CROP-SPECIFIC OUTLIER AUDIT")
print("-" * 60)
print("Total cleaned records:", len(df))
print("Flagged records:", len(outliers))
print("Percentage flagged:", round(
    len(outliers) / len(df) * 100, 2
), "%")

print("\n20 MOST EXTREME FLAGGED RECORDS")
print("-" * 60)
print(outliers[columns].head(20).round(4).to_string(index=False))

print("\nCROPS WITH MOST FLAGGED RECORDS")
print("-" * 60)
print(summary.head(15).round(3).to_string())

print("\nSaved:")
print(REPORT_DIR / "crop_outlier_audit.csv")
print(REPORT_DIR / "crop_outlier_summary.csv")
