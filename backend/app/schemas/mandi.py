from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class MandiAnalysisRequest(BaseModel):
    crop: str = Field(..., description="Crop name for mandi analysis")
    state: Optional[str] = Field("All", description="State filter or 'All'")
    user_price_override: Optional[float] = Field(None, gt=0, description="Farmer user-entered custom price (Rs./quintal)")

class ExperimentalForecastMetric(BaseModel):
    model_name: str
    status: str
    chronological_baseline_mae: float = Field(..., description="Naive Lag-1 Persistence MAE in Rs./quintal")
    hgb_test_mae: float = Field(..., description="HistGradientBoosting test MAE in Rs./quintal")
    verdict: str

class MandiAnalysisResponse(BaseModel):
    crop: str
    state: str
    selected_price_quintal: float
    price_source: str
    unit: str = "Rs./Quintal"
    historical_min: float
    historical_median: float
    historical_max: float
    date_range: str
    sample_size: int
    is_user_override: bool
    experimental_forecast: ExperimentalForecastMetric
