"""Create this model's soil sample using the shared, balanced SoilGrids cleaner."""
from pathlib import Path
import json
import sys

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE.parent / "clustering" / "preprocessing"))
from prepare_data import prepare as prepare_soil

def prepare():
    # Keep each model's processed data isolated even though both use the same source sample.
    data = prepare_soil()
    output = MODULE / "data" / "processed" / "soil_sample.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    # Store a model-local record of the sample size and fields used.
    summary = MODULE / "evaluation" / "preprocessing_summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({
        "source_directory": "DataSets/Soil Grid",
        "sample_rows": int(len(data)),
        "sample_rows_by_depth": data["source_depth_file"].value_counts().sort_index().to_dict(),
        "model_features": [
            "depth_top_cm", "depth_bottom_cm", "ph_h2o", "organic_carbon_g_kg",
            "total_nitrogen_g_kg", "sand_pct", "silt_pct", "clay_pct",
            "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct",
        ],
        "sample_columns": list(data.columns),
        "location_columns_used_for_holdout_only": ["latitude", "longitude"],
    }, indent=2) + "\n")
    return data

if __name__ == "__main__":
    print(f"Prepared {len(prepare())} soil rows for anomaly screening.")
