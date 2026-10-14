
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PROJECT_DIR.parent

RAW_FILE = (
    REPO_DIR / "DataSets"
    / "crop_production_haryana_punjab_1997_2019.csv"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW_FILE)
original_count = len(df)

# Preserve a copy for cleaning decisions.
df.columns = df.columns.str.strip()
df = df.drop_duplicates().copy()

# Standardize text columns without changing their meaning.
text_columns = [
    "State", "District", "Crop", "Season",
    "Area Units", "Production Units"
]

for col in text_columns:
    if col in df.columns:
        df[col] = df[col].astype("string").str.strip()

# Convert numerical columns.
for col in ["Area", "Production", "Yield"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert year labels such as 2001-02 into a start year.
year_text = df["Year"].astype("string")
df["YearStart"] = pd.to_numeric(
    year_text.str.extract(r"((?:19|20)\d{2})", expand=False),
    errors="coerce"
)

# Record all exclusion reasons before filtering.
reasons = pd.Series("", index=df.index, dtype="string")

def add_reason(mask, message):
    global reasons
    reasons.loc[mask] = reasons.loc[mask].apply(
        lambda old: f"{old}; {message}" if old else message
    )

required = [
    "State", "District", "Crop", "Season", "YearStart"
]

for col in required:
    add_reason(df[col].isna(), f"missing_{col}")

add_reason(
    df["Area"].isna() | ~np.isfinite(df["Area"]),
    "missing_or_invalid_area"
)
add_reason(
    df["Area"].notna() & (df["Area"] <= 0),
    "nonpositive_area"
)
add_reason(
    df["Yield"].isna() | ~np.isfinite(df["Yield"]),
    "missing_or_invalid_yield"
)
add_reason(
    df["Yield"].notna() & (df["Yield"] < 0),
    "negative_yield"
)
add_reason(
    df["Yield"].notna() & (df["Yield"] == 0),
    "zero_yield_review"
)

# This first version targets yield in tonnes per hectare.
# Do not treat production measured in bales as tonnes.
area_unit = df["Area Units"].str.lower()
production_unit = df["Production Units"].str.lower()

valid_area_units = area_unit.isin(
    ["hectare", "hectares", "ha"]
)
valid_production_units = production_unit.isin(
    ["tonne", "tonnes", "metric tonne", "metric tonnes",
     "metric ton", "metric tons"]
)

add_reason(~valid_area_units, "incompatible_area_unit")
add_reason(~valid_production_units, "incompatible_production_unit")

# Keep an audit file of all rows removed from the modelling dataset.
rejected = df.loc[reasons.ne("")].copy()
rejected["exclusion_reason"] = reasons.loc[reasons.ne("")]

rejected.to_csv(
    REPORT_DIR / "excluded_rows_audit.csv", index=False
)

# Keep only records that pass the initial cleaning rules.
clean = df.loc[reasons.eq("")].copy()

# Store YearStart as a numeric feature.
clean["YearStart"] = clean["YearStart"].astype(int)

# Flag extreme values for review, but do not automatically delete them.
q1 = clean["Yield"].quantile(0.25)
q3 = clean["Yield"].quantile(0.75)
iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

clean["Yield_Extreme_Flag"] = (
    (clean["Yield"] < lower_bound)
    | (clean["Yield"] > upper_bound)
)

clean.loc[clean["Yield_Extreme_Flag"]].to_csv(
    REPORT_DIR / "extreme_yield_review.csv", index=False
)

# Save the cleaned dataset separately.
clean.to_csv(
    OUTPUT_DIR / "crop_yield_cleaned.csv", index=False
)

summary = pd.DataFrame({
    "metric": [
        "original_rows",
        "rows_after_exact_duplicate_removal",
        "cleaned_rows",
        "excluded_rows",
        "extreme_yields_flagged",
        "cleaned_zero_yield_rows",
    ],
    "value": [
        original_count,
        original_count - df.duplicated().sum(),
        len(clean),
        len(rejected),
        int(clean["Yield_Extreme_Flag"].sum()),
        int((clean["Yield"] == 0).sum()),
    ],
})

summary.to_csv(
    REPORT_DIR / "cleaning_summary.csv", index=False
)

print("\n--- CLEANING SUMMARY ---")
print(summary.to_string(index=False))
print("\nCleaned data:", OUTPUT_DIR / "crop_yield_cleaned.csv")
print("Excluded-row audit:", REPORT_DIR / "excluded_rows_audit.csv")
print("Extreme-yield review:", REPORT_DIR / "extreme_yield_review.csv")
