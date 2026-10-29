from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.plan import CropPlan

class WhatIfRequest(BaseModel):
    base_plan: CropPlan
    price_change_pct: float = Field(0.0, ge=-80.0, le=200.0, description="Percentage change in price (e.g. +10 or -15)")
    yield_shock_pct: float = Field(0.0, ge=-80.0, le=100.0, description="Percentage change in yield (e.g. -20 for drought)")
    storage_months: int = Field(0, ge=0, le=12, description="Storage duration in months")
    area_override: Optional[float] = Field(None, gt=0, le=100000, description="Optional override for cultivated area (ha)")

class WhatIfResponse(BaseModel):
    crop: str
    scenario_description: str
    original_yield_t_ha: float
    simulated_yield_t_ha: float
    original_marketable_quintals: float
    simulated_marketable_quintals: float
    original_price_quintal: float
    simulated_price_quintal: float
    original_gross_revenue: float
    simulated_gross_revenue: float
    original_total_costs: float
    simulated_total_costs: float
    original_net_return: float
    simulated_net_return: float
    diff_net_return: float
    roi_percentage: float
    simulated_plan: CropPlan
