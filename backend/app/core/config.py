from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parents[3]  # AgriOptima-Project root
DATASETS_DIR = BASE_DIR / "DataSets"
CROP_MODEL_DIR = BASE_DIR / "models" / "crop_suitability" / "artifacts"
YIELD_MODEL_DIR = BASE_DIR / "models" / "crop_yield" / "artifacts"
POST_HARVEST_CSV = DATASETS_DIR / "post_harvest_loss_2022_haryana_punjab.csv"
MANDI_DIR = DATASETS_DIR / "india_mandi_prices_2000_2024"

# Model file paths
CROP_SUITABILITY_MODEL_PATH = CROP_MODEL_DIR / "crop_suitability_pipeline.pkl"
YIELD_RANDOM_FOREST_MODEL_PATH = YIELD_MODEL_DIR / "random_forest.joblib"
