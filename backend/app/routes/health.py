from fastapi import APIRouter
from app.services.model_service import model_service
from app.core.config import CROP_SUITABILITY_MODEL_PATH, YIELD_RANDOM_FOREST_MODEL_PATH

router = APIRouter()

@router.get("/health")
def get_health():
    """
    Returns application health, pipeline loading status, model versions, and metadata.
    """
    crop_loaded = model_service.crop_pipeline is not None
    yield_loaded = model_service.yield_pipeline is not None

    return {
        "status": "healthy" if (crop_loaded and yield_loaded) else "degraded",
        "app_name": "AgriOptima Connected Agricultural Intelligence",
        "version": "1.0.0",
        "models": {
            "crop_suitability": {
                "selected_model": "Support Vector Machine (SVC)",
                "pipeline_loaded": crop_loaded,
                "file_path": str(CROP_SUITABILITY_MODEL_PATH),
                "historical_accuracy": "79.87%",
                "supported_crops_count": len(model_service.crop_pipeline.classes_) if crop_loaded else 0,
                "probability_calibration": False
            },
            "crop_yield": {
                "selected_model": "Random Forest Regressor (200 trees, max_depth=15)",
                "pipeline_loaded": yield_loaded,
                "file_path": str(YIELD_RANDOM_FOREST_MODEL_PATH),
                "historical_mae_tonnes_per_ha": 2.10,
                "supported_states": model_service.supported_states,
                "supported_districts_count": len(model_service.supported_districts),
                "supported_crops_count": len(model_service.supported_crops),
                "supported_seasons": model_service.supported_seasons
            },
            "mandi_forecasting": {
                "experimental_model": "HistGradientBoostingRegressor",
                "status": "Experimental only (Excluded from production planning; persistence baseline outperformed it with MAE 161.09 vs 389.71 Rs./qtl)"
            }
        },
        "metadata": {
            "supported_districts": model_service.supported_districts,
            "supported_crops": model_service.supported_crops,
            "supported_seasons": model_service.supported_seasons
        }
    }
