from fastapi import APIRouter, HTTPException
from app.schemas.plan import FarmProfile, PlanResponse
from app.services.planning_engine import planning_engine

router = APIRouter()

@router.post("/plan", response_model=PlanResponse)
def generate_connected_plan(profile: FarmProfile):
    """
    Executes the complete connected workflow:
    Farm Profile -> Crop Suitability SVM -> Yield Random Forest -> Production & Unit Conversions ->
    Post-Harvest Losses -> Mandi Prices -> Cultivation & Logistics Costs -> Net Return & Ranked Plans.
    """
    try:
        return planning_engine.generate_full_plan(profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning generation failed: {str(e)}")
