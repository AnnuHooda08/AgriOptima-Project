"""post_harvest_loss/tests/test_post_harvest_loss.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_loss_model_predicts():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/post_harvest_loss_rf.joblib')
    x=pd.DataFrame([dict(state='Haryana',crop='Bajra',loss_type='Farm Operations',stage='Harvesting')])
    value=p['model'].predict(x)[0]
    assert value>=0
