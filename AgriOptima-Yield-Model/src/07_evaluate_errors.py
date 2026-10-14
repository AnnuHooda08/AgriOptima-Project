
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
PREDICTIONS_FILE = PROJECT_DIR / "reports" / "test_predictions.csv"
REPORT_DIR = PROJECT_DIR / "reports"

df = pd.read_csv(PREDICTIONS_FILE)

model_columns = {
    "Linear Regression": "Predicted_linear_regression",
    "Random Forest": "Predicted_random_forest",
}

required = [
    "State", "District", "Crop", "Season",
    "YearStart", "Yield",
    *model_columns.values(),
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# 1. Understand the distribution of actual test yields
print("TEST YIELD DISTRIBUTION")
print("-" * 60)
print(df["Yield"].describe(percentiles=[0.90, 0.95, 0.99]).to_string())

# 2. Compare errors for Linear Regression and Random Forest
for name, col in model_columns.items():
    error = df["Yield"] - df[col]
    absolute_error = error.abs()

    print(f"\n{name}")
    print("-" * 60)
    print("MAE:", round(absolute_error.mean(), 4))
    print("RMSE:", round(np.sqrt((error ** 2).mean()), 4))
    print("Median absolute error:", round(absolute_error.median(), 4))
    print("90th percentile absolute error:",
          round(absolute_error.quantile(0.90), 4))
    print("Maximum absolute error:", round(absolute_error.max(), 4))

# 3. Find records with the largest Random Forest errors
df["RF_Absolute_Error"] = (
    df["Yield"] - df["Predicted_random_forest"]
).abs()

worst = df.sort_values(
    "RF_Absolute_Error", ascending=False
).head(20)

columns = [
    "State", "District", "Crop", "Season", "YearStart",
    "Yield", "Predicted_random_forest",
    "Predicted_linear_regression", "RF_Absolute_Error",
]

worst[columns].to_csv(
    REPORT_DIR / "worst_random_forest_predictions.csv",
    index=False,
)

print("\n20 LARGEST RANDOM FOREST ERRORS")
print(worst[columns].to_string(index=False))

# 4. Compare models by crop
crop_results = []

for crop, group in df.groupby("Crop"):
    row = {
        "Crop": crop,
        "Test_Rows": len(group),
    }

    for name, col in model_columns.items():
        errors = group["Yield"] - group[col]
        key = name.replace(" ", "_")
        row[f"{key}_MAE"] = errors.abs().mean()
        row[f"{key}_RMSE"] = np.sqrt((errors ** 2).mean())

    crop_results.append(row)

crop_report = pd.DataFrame(crop_results)
crop_report.to_csv(
    REPORT_DIR / "model_errors_by_crop.csv",
    index=False,
)

print("\nCROP-WISE ERROR REPORT")
print(crop_report.sort_values(
    "Random_Forest_MAE", ascending=False
).head(15).round(4).to_string(index=False))

print("\nSaved:")
print(REPORT_DIR / "worst_random_forest_predictions.csv")
print(REPORT_DIR / "model_errors_by_crop.csv")
