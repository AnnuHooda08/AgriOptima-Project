
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR / "data" / "processed"
    / "crop_yield_cleaned.csv"
)
EDA_DIR = PROJECT_DIR / "reports" / "eda"
EDA_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

sns.set_theme(style="whitegrid")

# 1. Yield distribution
plt.figure(figsize=(9, 5))
sns.histplot(data=df, x="Yield", bins=40, kde=True)
plt.title("Distribution of Crop Yield")
plt.xlabel("Yield (tonnes per hectare)")
plt.ylabel("Number of records")
plt.tight_layout()
plt.savefig(EDA_DIR / "01_yield_distribution.png", dpi=150)
plt.close()

# 2. Yield by state
plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x="State", y="Yield")
plt.title("Crop Yield Distribution by State")
plt.xlabel("State")
plt.ylabel("Yield (tonnes per hectare)")
plt.tight_layout()
plt.savefig(EDA_DIR / "02_yield_by_state.png", dpi=150)
plt.close()

# 3. Median yield by crop: show the 15 crops with most records
top_crops = (
    df["Crop"].value_counts().head(15).index
)
crop_data = df[df["Crop"].isin(top_crops)]

crop_order = (
    crop_data.groupby("Crop")["Yield"]
    .median()
    .sort_values()
    .index
)

plt.figure(figsize=(11, 7))
sns.boxplot(
    data=crop_data,
    x="Yield",
    y="Crop",
    order=crop_order
)
plt.title("Yield by Crop (15 Most Frequently Recorded Crops)")
plt.xlabel("Yield (tonnes per hectare)")
plt.ylabel("Crop")
plt.tight_layout()
plt.savefig(EDA_DIR / "03_yield_by_crop.png", dpi=150)
plt.close()

# 4. Yield by season
season_order = (
    df.groupby("Season")["Yield"]
    .median()
    .sort_values()
    .index
)

plt.figure(figsize=(10, 5))
sns.boxplot(data=df, x="Season", y="Yield", order=season_order)
plt.title("Crop Yield by Season")
plt.xlabel("Season")
plt.ylabel("Yield (tonnes per hectare)")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(EDA_DIR / "04_yield_by_season.png", dpi=150)
plt.close()

# 5. Yearly median yield
yearly = (
    df.groupby("YearStart", as_index=False)
    .agg(
        median_yield=("Yield", "median"),
        record_count=("Yield", "size")
    )
)

yearly.to_csv(EDA_DIR / "yearly_yield_summary.csv", index=False)

plt.figure(figsize=(10, 5))
sns.lineplot(data=yearly, x="YearStart", y="median_yield", marker="o")
plt.title("Median Reported Yield by Year")
plt.xlabel("Year")
plt.ylabel("Median yield (tonnes per hectare)")
plt.tight_layout()
plt.savefig(EDA_DIR / "05_yield_by_year.png", dpi=150)
plt.close()

# 6. Correlation between numerical columns
numeric_cols = [
    col for col in ["YearStart", "Area", "Yield"]
    if col in df.columns
]

correlation = df[numeric_cols].corr()
correlation.to_csv(EDA_DIR / "numeric_correlation.csv")

plt.figure(figsize=(7, 5))
sns.heatmap(
    correlation,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    vmin=-1,
    vmax=1
)
plt.title("Correlation Between Numerical Variables")
plt.tight_layout()
plt.savefig(EDA_DIR / "06_numeric_correlation.png", dpi=150)
plt.close()

# 7. Summary tables
df.groupby("Crop").agg(
    records=("Yield", "size"),
    mean_yield=("Yield", "mean"),
    median_yield=("Yield", "median"),
    min_yield=("Yield", "min"),
    max_yield=("Yield", "max")
).sort_values("records", ascending=False).to_csv(
    EDA_DIR / "crop_summary.csv"
)

df.groupby(["State", "Season"]).agg(
    records=("Yield", "size"),
    median_yield=("Yield", "median"),
    mean_yield=("Yield", "mean")
).to_csv(EDA_DIR / "state_season_summary.csv")

print("EDA complete.")
print("Charts and tables saved in:", EDA_DIR)
print("\nDataset shape:", df.shape)
print("\nYield summary:")
print(df["Yield"].describe())
