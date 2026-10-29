"""
models/crop_suitability/config.py

Centralised configuration for the crop suitability module.
All paths are relative to the repository root so the module works
from any working directory and on any machine.
"""

from pathlib import Path

# Repository root = two levels above this file (models/crop_suitability/config.py)
REPO_ROOT = Path(__file__).resolve().parents[2]

MODULE_DIR  = REPO_ROOT / "models" / "crop_suitability"
ARTIFACT    = MODULE_DIR / "artifacts" / "crop_suitability_pipeline.pkl"

# Raw training data (original file, never modified)
RAW_DATA    = REPO_ROOT / "DataSets" / "crop_suitability.csv"

# Processed data (output of preprocessing scripts, stored separately)
PROCESSED_DATA = MODULE_DIR / "data" / "processed" / "crop_suitability_processed.csv"

# ── Input feature specification ───────────────────────────────────────────────
# These names and order must match exactly what the pipeline was trained on.
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COLUMN   = "label"

# ── Feature ranges (used for input validation) ────────────────────────────────
FEATURE_RANGES = {
    "N":           (0.0,  300.0),
    "P":           (0.0,  300.0),
    "K":           (0.0,  300.0),
    "temperature": (-10.0, 60.0),
    "humidity":    (0.0,  100.0),
    "ph":          (0.0,   14.0),
    "rainfall":    (0.0, 2000.0),
}

# ── Model metadata ────────────────────────────────────────────────────────────
# The saved pipeline contains StandardScaler + SVC(C=1, probability=False).
# Do NOT re-scale inputs before passing them to the pipeline.
ALGORITHM              = "Support Vector Machine (SVC, C=1, kernel=rbf)"
PROBABILITY_SUPPORTED  = False   # pipeline was trained with probability=False
HISTORICAL_ACCURACY    = 0.7987  # preserved from original evaluation
TEST_SPLIT_YEAR        = None    # soil dataset; random 80/20 split was used
SKLEARN_TRAIN_VERSION  = "1.7.2"
