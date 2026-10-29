from fastapi import APIRouter, HTTPException
from app.schemas.what_if import WhatIfRequest, WhatIfResponse
from app.services.planning_engine import planning_engine

router = APIRouter()

@router.post("/what-if", response_model=WhatIfResponse)
def simulate_what_if_scenario(req: WhatIfRequest):
    """
    Simulates what-if sensitivity adjustments:
    Adjusts market prices (+/- %), yield shocks (+/- %), storage durations, and land area allocations.
    Recalculates exact financial and production impacts.
    """
    try:
        return planning_engine.simulate_what_if(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-If simulation failed: {str(e)}")
