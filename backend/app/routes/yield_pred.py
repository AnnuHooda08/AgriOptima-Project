from fastapi import APIRouter, HTTPException
from app.schemas.yield_pred import YieldPredictionRequest, YieldPredictionResponse
from app.services.model_service import model_service

router = APIRouter()

@router.post("/yield-prediction", response_model=YieldPredictionResponse)
def predict_crop_yield(req: YieldPredictionRequest):
    """
    Predicts yield in tonnes per hectare using the saved Random Forest pipeline.
    Calculates estimated production in tonnes and quintals.
    """
    try:
        return model_service.predict_yield(
            state=req.state,
            district=req.district,
            crop=req.crop,
            season=req.season,
            year=req.year,
            area=req.area
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yield prediction failed: {str(e)}")
