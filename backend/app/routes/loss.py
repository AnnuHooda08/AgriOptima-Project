from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.loss_service import model_loss, loss_bundle
router=APIRouter()
class LossRequest(BaseModel):
    crop:str
    state:str
@router.get('/loss-options')
def options():
    bundle=loss_bundle()
    encoder=bundle['model'].named_steps['preprocessor'].named_transformers_['categories'].named_steps['encoder']
    categories=dict(zip(bundle['features'],encoder.categories_))
    excluded=('milk','meat','fish','egg','poultry')
    return {'states':list(categories['state']), 'crops':[str(c) for c in categories['crop'] if not any(x in str(c).lower() for x in excluded)]}
@router.post('/loss-analysis')
def predict(req:LossRequest):
    value=model_loss(req.crop,req.state)
    if value is None: raise HTTPException(422,'This crop and state are outside the loss model training categories.')
    return {'crop':req.crop,'state':req.state,'loss_percentage':value,
            'source':'Estimated overall loss using the model trained on published NABCONS study values.'}
