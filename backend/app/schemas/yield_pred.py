from typing import Optional
from pydantic import BaseModel, Field

class YieldPredictionRequest(BaseModel):
    state: str = Field(..., description="Indian State (e.g. Haryana, Punjab)")
    district: str = Field(..., description="District Name (e.g. Ambala, Karnal, Ludhiana)")
    crop: str = Field(..., description="Crop Name (e.g. Rice, Wheat, Maize, Cotton(lint), Bajra)")
    season: str = Field(..., description="Season: Kharif, Rabi, or Whole Year")
    year: int = Field(2024, ge=1990, le=2030, description="Reference agricultural year")
    area: float = Field(..., gt=0, le=100000, description="Cultivated land area in hectares")

class YieldPredictionResponse(BaseModel):
    state: str
    district: str
    crop: str
    season: str
    year: int
    area_ha: float
    predicted_yield_tonnes_per_ha: float
    estimated_production_tonnes: float
    estimated_production_quintals: float
    model_name: str
    evaluation_rationale: str
    is_supported_crop: bool
    is_supported_district: bool
    validation_message: Optional[str] = None
