
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "reports"
    / "log_target_validation_predictions.csv"
)

REPORT_DIR = PROJECT_DIR / "reports"

df = pd.read_csv(INPUT_FILE)

prediction_columns = {
    "Original_Target": "Predicted_original",
    "Log_Target": "Predicted_log",
}

for name, prediction_col in prediction_columns.items():
    df[f"{name}_Error"] = (
        df["Yield"] - df[prediction_col]
    )
    df[f"{name}_Absolute_Error"] = (
        df[f"{name}_Error"].abs()
    )

print("VALIDATION YIELD DISTRIBUTION")
print("-" * 65)
print(
    df["Yield"]
    .describe(percentiles=[0.90, 0.95, 0.99])
    .to_string()
)

for name in prediction_columns:
    print(f"\n{name}: LARGEST ERRORS")
    print("-" * 65)

    worst = df.nlargest(
        15, f"{name}_Absolute_Error"
    )

    columns = [
        "State", "District", "Crop", "Season",
        "YearStart", "Yield",
        prediction_columns[name],
        f"{name}_Absolute_Error",
    ]

    print(worst[columns].round(4).to_string(index=False))

# Save the full row-level diagnostic report.
df.to_csv(
    REPORT_DIR / "log_target_error_details.csv",
    index=False,
)

# Compare errors by crop.
crop_rows = []

for crop, group in df.groupby("Crop"):
    row = {
        "Crop": crop,
        "Validation_Rows": len(group),
    }

    for name, prediction_col in prediction_columns.items():
        errors = (
            group["Yield"] - group[prediction_col]
        )

        row[f"{name}_MAE"] = errors.abs().mean()
        row[f"{name}_RMSE"] = np.sqrt(
            (errors ** 2).mean()
        )

    crop_rows.append(row)

crop_report = pd.DataFrame(crop_rows)

crop_report = crop_report.sort_values(
    "Log_Target_MAE", ascending=False
)

crop_report.to_csv(
    REPORT_DIR / "log_target_errors_by_crop.csv",
    index=False,
)

print("\nCROP-WISE ERRORS: LOG-TARGET MODEL")
print("-" * 65)
print(crop_report.head(15).round(4).to_string(index=False))

print("\nSaved:")
print(REPORT_DIR / "log_target_error_details.csv")
print(REPORT_DIR / "log_target_errors_by_crop.csv")
