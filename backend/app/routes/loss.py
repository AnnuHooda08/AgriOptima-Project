from fastapi import APIRouter
from pydantic import BaseModel
from app.services.planning_engine import dataset_loss
from app.services.loss_service import model_loss

router = APIRouter()

class LossRequest(BaseModel):
    crop: str
    state: str

@router.post("/loss-analysis")
def loss_analysis(req: LossRequest):
    reference, stages, source = dataset_loss(req.crop, req.state)
    estimate = model_loss(req.crop, req.state)
    return {"published_loss_pct": round(reference, 3), "published_source": source,
        "model_loss_pct": estimate, "model_available": estimate is not None,
        "note": "Grouped historical test MAE: 0.344 percentage points across all record types, and 1.040 points for overall totals alone. The stage-median baseline scores 0.356 overall. These are study-value estimates, not verified farm outcomes."}
