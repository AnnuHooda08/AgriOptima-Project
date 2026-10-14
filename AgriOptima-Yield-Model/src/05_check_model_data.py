
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

print("DATASET OVERVIEW")
print("-" * 50)
print("Shape:", df.shape)
print("Year range:", df["YearStart"].min(), "-", df["YearStart"].max())
print("Unique crops:", df["Crop"].nunique())
print("Unique districts:", df["District"].nunique())
print("Unique states:", df["State"].nunique())
print("Missing values:\n", df.isna().sum())

print("\nYIELD SUMMARY")
print(df["Yield"].describe())

print("\nRECORDS PER YEAR")
print(df.groupby("YearStart").size().to_string())

# Proposed chronological split: latest 20% of distinct years for testing.
years = sorted(df["YearStart"].dropna().unique())

if len(years) < 5:
    raise ValueError("Not enough distinct years for a chronological split.")

split_index = max(1, int(len(years) * 0.8))
split_index = min(split_index, len(years) - 1)
test_years = years[split_index:]
cutoff_year = test_years[0]

train = df[df["YearStart"] < cutoff_year]
test = df[df["YearStart"] >= cutoff_year]

print("\nPROPOSED CHRONOLOGICAL SPLIT")
print("Training years:", train["YearStart"].min(), "-", train["YearStart"].max())
print("Training rows:", len(train))
print("Testing years:", test["YearStart"].min(), "-", test["YearStart"].max())
print("Testing rows:", len(test))

print("\nCROP COVERAGE")
train_crops = set(train["Crop"])
test_crops = set(test["Crop"])

print("Crops in test set:", len(test_crops))
print("Test crops absent from training:", sorted(test_crops - train_crops))

print("\nFEATURE CATEGORIES")
for col in ["State", "District", "Crop", "Season"]:
    print(f"{col}: {df[col].nunique()} unique values")

# Save split metadata for review; no model is trained here.
summary = pd.DataFrame([
    {
        "split": "train",
        "rows": len(train),
        "first_year": train["YearStart"].min(),
        "last_year": train["YearStart"].max(),
    },
    {
        "split": "test",
        "rows": len(test),
        "first_year": test["YearStart"].min(),
        "last_year": test["YearStart"].max(),
    },
])
summary.to_csv(REPORT_DIR / "proposed_temporal_split.csv", index=False)

print("\nSaved split report:", REPORT_DIR / "proposed_temporal_split.csv")
print("No models trained.")
