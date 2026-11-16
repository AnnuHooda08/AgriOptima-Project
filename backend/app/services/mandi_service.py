import logging
from typing import Dict, Any, Optional
from app.schemas.mandi import MandiAnalysisResponse, ExperimentalForecastMetric

logger = logging.getLogger(__name__)

from functools import lru_cache
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from app.core.config import DATASETS_DIR, BASE_DIR

CROP_FILES = {
    "Masoor": "Lentil (Masur)(Whole)", "Guar seed": "Guar Seed(Cluster Beans Seed)",
    "Horse-gram": "Kulthi(Horse Gram)",
    "Rice": "Paddy(Dhan)(Common)", "Arhar/Tur": "Arhar (Tur-Red Gram)(Whole)",
    "Peas & beans (Pulses)": "Peas(Dry)", "Gram": "Bengal Gram(Gram)(Whole)",
    "Moong(Green Gram)": "Green Gram (Moong)(Whole)", "Urad": "Black Gram (Urd Beans)(Whole)",
    "Rapeseed &Mustard": "Mustard", "Cotton(lint)": "Cotton", "Soyabean": "Soyabean",
}

@lru_cache(maxsize=64)
def dataset_prices(crop):
    # Cache the cleaned table so repeated requests do not reread large CSVs.
    name = CROP_FILES.get(crop, crop)
    path = DATASETS_DIR / "india_mandi_prices_2000_2024" / (name + ".csv")
    if not path.is_file():
        raise ValueError("No historical market data for this crop. Enter a local offer.")
    columns = ["State Name", "District Name", "Market Name", "Modal Price (Rs./Quintal)", "Reported Date"]
    data = pd.read_csv(path, usecols=lambda col: col in columns or col == "Modal Price").drop_duplicates()
    if columns[3] not in data.columns:
        data = data.rename(columns={"Modal Price": columns[3]})
    data["price"] = pd.to_numeric(data[columns[3]], errors="coerce")
    data["date"] = pd.to_datetime(data[columns[4]], format="%d %b %Y", errors="coerce")
    data["date"] = data["date"].fillna(pd.to_datetime(data[columns[4]], format="%Y-%m-%d", errors="coerce"))
    clean = data.loc[data.date.notna() & np.isfinite(data.price) & data.price.gt(0)].copy()
    if clean.empty:
        raise ValueError("No valid historical prices for this crop. Enter a local offer.")
    return clean

@lru_cache(maxsize=1)
def maize_forecast():
    # Use the saved model's actual forecast origin, not today's calendar month.
    path = BASE_DIR / "backend/saved_models/maize_price_extended_linear.joblib"
    if not path.exists():
        return None
    bundle = joblib.load(path)
    monthly = pd.read_csv(BASE_DIR / "results/mandi_prices/monthly_data.csv")
    monthly["date"] = pd.to_datetime(monthly["date"])
    target = pd.Timestamp(bundle["training_last_month"]) + pd.offsets.MonthBegin(1)
    row = monthly.loc[monthly.date.eq(target), bundle["features"]]
    if row.empty or row.isna().any().any():
        return None
    value = float(bundle["model"].predict(row)[0])
    return round(value, 2) if np.isfinite(value) and value > 0 else None

class MandiService:
    @staticmethod
    def get_mandi_analysis(crop, state="All", user_price_override=None, district=None):
        try:
            data = dataset_prices(crop)
        except ValueError:
            if user_price_override is None:
                raise
            return MandiAnalysisResponse(crop=crop, state=state or "All", selected_price_quintal=user_price_override,
                price_source="Farmer-entered local offer; historical dataset unavailable.", historical_min=user_price_override,
                historical_median=user_price_override, historical_max=user_price_override, date_range="", sample_size=0,
                is_user_override=True)
        scope = "national dataset"
        if state and state != "All":
            regional = data[data["State Name"].str.casefold().eq(state.casefold())]
            if not regional.empty:
                data, scope = regional, state
                if district:
                    local = data[data["District Name"].str.casefold().eq(district.casefold())]
                    if not local.empty:
                        data, scope = local, district + ", " + state
        # Latest available recorded month in the matched location, not a live quote.
        latest = data.date.max().to_period("M")
        recent = data[data.date.dt.to_period("M").eq(latest)]
        median = round(float(recent.price.median()), 2)
        source = f"Historical dataset: {scope}; median of {len(recent):,} reports from the latest available recorded month. Not live."
        if user_price_override is not None:
            source = "Farmer-entered local offer. " + source
        return MandiAnalysisResponse(crop=crop, state=state or "All", selected_price_quintal=user_price_override if user_price_override is not None else median,
            price_source=source, historical_min=float(recent.price.min()), historical_median=median,
            historical_max=float(recent.price.max()), date_range=str(latest), sample_size=len(recent),
            is_user_override=user_price_override is not None, market_scope=scope,
            forecast_price_quintal=maize_forecast(),
            forecast_note="Historical one-month-ahead research estimate for national maize. Not a local or current quote. Validation favoured the previous-month baseline.")

mandi_service = MandiService()
