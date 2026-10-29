from fastapi import APIRouter, HTTPException
from app.schemas.crop import CropRecommendationRequest, CropRecommendationResponse
from app.services.model_service import model_service

router = APIRouter()

@router.post("/crop-recommendation", response_model=CropRecommendationResponse)
def recommend_crop(req: CropRecommendationRequest):
    """
    Evaluates soil N-P-K, pH, and climate parameters using the saved SVM pipeline.
    Returns primary recommended crop and alternative candidate ranking based on decision boundary margin.
    """
    try:
        return model_service.predict_crop_suitability(
            N=req.N,
            P=req.P,
            K=req.K,
            temperature=req.temperature,
            humidity=req.humidity,
            ph=req.ph,
            rainfall=req.rainfall
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crop suitability evaluation failed: {str(e)}")
