
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PROJECT_DIR.parent

DATA_FILE = (
    REPO_DIR
    / "DataSets"
    / "crop_production_haryana_punjab_1997_2019.csv"
)

REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_FILE}\n"
        "Check the folder and filename."
    )

df = pd.read_csv(DATA_FILE)

print("\n--- DATASET SHAPE ---")
print(df.shape)

print("\n--- FIRST FIVE ROWS ---")
print(df.head())

print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATE ROWS ---")
print(df.duplicated().sum())

print("\n--- NUMERICAL SUMMARY ---")
print(df.describe(include="all").T)

print("\n--- CATEGORICAL VALUES ---")
for col in ["State", "Crop", "Season", "Area Units",
            "Production Units"]:
    if col in df.columns:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(20))

# Save an inspection report
profile = pd.DataFrame({
    "column": df.columns,
    "dtype": [str(df[c].dtype) for c in df.columns],
    "missing_count": [df[c].isna().sum() for c in df.columns],
    "missing_percent": [
        round(df[c].isna().mean() * 100, 2)
        for c in df.columns
    ],
    "unique_values": [df[c].nunique(dropna=True) for c in df.columns],
})

profile.to_csv(REPORT_DIR / "data_profile.csv", index=False)

print("\nProfile saved to reports/data_profile.csv")
