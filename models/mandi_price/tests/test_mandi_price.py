"""mandi_price/tests/test_mandi_price.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_saved_price_model_predicts():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/maize_price_hgb.joblib')
    x=pd.DataFrame([dict(lag_1=1000,lag_2=990,lag_3=980,lag_12=900,month=1,year=2025)])
    assert p['model'].predict(x).shape==(1,)
