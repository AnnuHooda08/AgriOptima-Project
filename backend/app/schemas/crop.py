from typing import List, Dict, Any
from pydantic import BaseModel, Field

class CropRecommendationRequest(BaseModel):
    N: float = Field(..., ge=0, le=300, description="Nitrogen content in soil (kg/ha)")
    P: float = Field(..., ge=0, le=300, description="Phosphorus content in soil (kg/ha)")
    K: float = Field(..., ge=0, le=300, description="Potassium content in soil (kg/ha)")
    temperature: float = Field(..., ge=-10, le=60, description="Temperature in degrees Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity in percentage")
    ph: float = Field(..., ge=0, le=14, description="Soil pH value")
    rainfall: float = Field(..., ge=0, le=2000, description="Rainfall in mm")

class CandidateCrop(BaseModel):
    crop: str
    decision_score: float = Field(..., description="Decision boundary distance heuristic (not calibrated probability)")
    is_top_choice: bool

class CropRecommendationResponse(BaseModel):
    recommended_crop: str
    decision_boundary_score: float
    probability_supported: bool = False
    evaluation_note: str
    candidate_ranking: List[CandidateCrop]
    input_features: Dict[str, float]
