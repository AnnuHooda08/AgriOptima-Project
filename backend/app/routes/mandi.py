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
            crop=req.crop, state=req.state, user_price_override=req.user_price_override, district=req.district
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mandi analysis failed: {str(e)}")

from pydantic import BaseModel
from app.services.market_forecast_service import market_options, predict_market
class ForecastRequest(BaseModel):
    crop: str
    state: str
@router.get('/market-options')
def forecast_options(): return market_options()
@router.post('/market-forecast')
def forecast(req:ForecastRequest):
    try: return predict_market(req.crop,req.state)
    except ValueError as error: raise HTTPException(422,str(error))
