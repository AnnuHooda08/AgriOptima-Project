"""
models/crop_suitability/preprocessing/feature_validation.py

Validates input data before it is passed to the suitability pipeline.
Returns a validated DataFrame or raises ValueError with a clear message.
"""

from typing import Dict, Any
import pandas as pd
import sys
from pathlib import Path

# Allow importing config regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from crop_suitability.config import FEATURE_COLUMNS, FEATURE_RANGES


def validate_single_input(raw: Dict[str, Any]) -> pd.DataFrame:
    """
    Validate a single prediction request dictionary and return a 1-row DataFrame
    with columns in the exact order the pipeline expects.

    Parameters
    ----------
    raw : dict  Keys: N, P, K, temperature, humidity, ph, rainfall  (all numeric)

    Returns
    -------
    pd.DataFrame  Shape (1, 7), columns in FEATURE_COLUMNS order.

    Raises
    ------
    ValueError   If a required field is missing or out of the allowed range.
    """
    missing = [col for col in FEATURE_COLUMNS if col not in raw]
    if missing:
        raise ValueError(f"Missing required input fields: {missing}")

    row = {}
    for col in FEATURE_COLUMNS:
        try:
            val = float(raw[col])
        except (TypeError, ValueError):
            raise ValueError(f"Field '{col}' must be numeric; received: {raw[col]!r}")

        lo, hi = FEATURE_RANGES[col]
        if not (lo <= val <= hi):
            raise ValueError(
                f"Field '{col}' = {val} is outside the allowed range [{lo}, {hi}]."
            )
        row[col] = val

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def validate_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate a multi-row DataFrame.  Returns a cleaned DataFrame with
    columns reordered to FEATURE_COLUMNS, or raises ValueError.
    """
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[FEATURE_COLUMNS].copy()
    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        lo, hi = FEATURE_RANGES[col]
        out = df[(df[col] < lo) | (df[col] > hi)]
        if not out.empty:
            raise ValueError(
                f"Column '{col}' has {len(out)} values outside [{lo}, {hi}]. "
                f"Example invalid rows:\n{out.head(3)}"
            )

    if df.isnull().any().any():
        raise ValueError("After conversion, some values are NaN. Check input types.")

    return df
