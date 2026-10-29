from fastapi import APIRouter, HTTPException
from app.schemas.mandi import MandiAnalysisRequest, MandiAnalysisResponse
from app.services.mandi_service import mandi_service

router = APIRouter()

@router.post("/mandi-analysis", response_model=MandiAnalysisResponse)
def get_mandi_analysis(req: MandiAnalysisRequest):
    """
    Returns historical mandi prices, date ranges, MSP references, and experimental benchmark comparison.
    Allows user price override with clear transparency.
    """
    try:
        return mandi_service.get_mandi_analysis(
            crop=req.crop,
            state=req.state,
            user_price_override=req.user_price_override
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mandi analysis failed: {str(e)}")
