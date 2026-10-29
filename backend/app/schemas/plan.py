from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class FarmProfile(BaseModel):
    state: str = Field("Haryana", description="State name")
    district: str = Field("Ambala", description="District name")
    area_ha: float = Field(2.0, gt=0, description="Cultivated land area in hectares")
    season: str = Field("Kharif", description="Season (Kharif, Rabi, Whole Year)")
    N: float = Field(90.0, ge=0, le=300, description="Nitrogen (kg/ha)")
    P: float = Field(42.0, ge=0, le=300, description="Phosphorus (kg/ha)")
    K: float = Field(43.0, ge=0, le=300, description="Potassium (kg/ha)")
    temperature: float = Field(25.0, description="Temperature (°C)")
    humidity: float = Field(80.0, ge=0, le=100, description="Relative humidity (%)")
    ph: float = Field(6.5, ge=0, le=14, description="Soil pH")
    rainfall: float = Field(200.0, ge=0, description="Rainfall (mm)")
    storage_months: int = Field(0, ge=0, le=12, description="Delayed sale storage duration in months")
    user_price_override: Optional[float] = Field(None, gt=0, description="User custom mandi price (Rs/quintal)")

class CropPlan(BaseModel):
    crop: str
    suitable: bool
    suitability_rank: int
    predicted_yield_tonnes_per_ha: float
    cultivated_area_ha: float
    gross_production_tonnes: float
    gross_production_quintals: float
    loss_stage_breakdown: Dict[str, float]
    total_loss_percentage: float
    marketable_production_quintals: float
    applicable_price_per_quintal: float
    price_source: str
    gross_revenue_rs: float
    cultivation_cost_rs: float
    transport_cost_rs: float
    storage_cost_rs: float
    packaging_cost_rs: float
    total_costs_rs: float
    net_return_rs: float
    net_return_per_ha_rs: float
    roi_percentage: float
    feasibility_notes: List[str]

class PlanResponse(BaseModel):
    primary_crop: str
    selected_plan: CropPlan
    alternative_plans: List[CropPlan]
    formulas_and_assumptions: Dict[str, str]
