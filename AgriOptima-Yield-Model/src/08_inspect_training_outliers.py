
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "crop_yield_model_data.csv"
)

REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# Only inspect years used for model training
train = df[df["YearStart"] <= 2014].copy()

print("TRAINING DATA YIELD DISTRIBUTION")
print("-" * 60)
print(
    train["Yield"]
    .describe(percentiles=[0.90, 0.95, 0.99, 0.995])
    .to_string()
)

# Show the 30 highest training yields
highest = train.sort_values(
    "Yield", ascending=False
).head(30)

columns = [
    "State", "District", "Crop",
    "Season", "YearStart", "Area", "Yield"
]

print("\n30 HIGHEST TRAINING YIELDS")
print("-" * 60)
print(highest[columns].to_string(index=False))

highest[columns].to_csv(
    REPORT_DIR / "highest_training_yields.csv",
    index=False
)

# Summarize high yields by crop
crop_summary = (
    train.groupby("Crop")["Yield"]
    .agg(
        Records="count",
        Median="median",
        Mean="mean",
        Maximum="max"
    )
    .sort_values("Maximum", ascending=False)
)

print("\nCROPS WITH THE HIGHEST RECORDED YIELDS")
print("-" * 60)
print(crop_summary.head(20).round(3).to_string())

crop_summary.to_csv(
    REPORT_DIR / "training_yield_summary_by_crop.csv"
)

print("\nReports saved:")
print(REPORT_DIR / "highest_training_yields.csv")
print(REPORT_DIR / "training_yield_summary_by_crop.csv")

