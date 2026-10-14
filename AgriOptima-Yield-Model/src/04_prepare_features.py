
from pathlib import Path

import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "data" / "processed" / "crop_yield_cleaned.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load the validated dataset
df = pd.read_csv(INPUT_FILE)

# Confirm required columns exist
required_columns = [
    "State", "District", "Crop", "Season",
    "YearStart", "Area", "Yield", "Production"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Define target and candidate features
target = "Yield"

candidate_features = [
    "State",
    "District",
    "Crop",
    "Season",
    "YearStart",
    "Area",
]

# Build a modelling dataset without Production
model_df = df[candidate_features + [target]].copy()

# Validate the modelling dataset
assert model_df[target].notna().all()
assert (model_df[target] > 0).all()
assert model_df[candidate_features].notna().all().all()

# Save prepared data
output_file = OUTPUT_DIR / "crop_yield_model_data.csv"
model_df.to_csv(output_file, index=False)

# Save feature documentation
feature_info = pd.DataFrame({
    "column": candidate_features + [target],
    "role": ["input"] * len(candidate_features) + ["target"],
    "data_type": [
        str(model_df[col].dtype)
        for col in candidate_features + [target]
    ],
    "unique_values": [
        model_df[col].nunique()
        for col in candidate_features + [target]
    ],
})

feature_info.to_csv(REPORT_DIR / "feature_profile.csv", index=False)

print("Feature preparation complete.")
print("Dataset shape:", model_df.shape)
print("Input features:", candidate_features)
print("Target:", target)
print("Production excluded from model inputs.")
print("Saved dataset:", output_file)
print("Saved feature profile:", REPORT_DIR / "feature_profile.csv")
print("\nPrepared data preview:")
print(model_df.head())
