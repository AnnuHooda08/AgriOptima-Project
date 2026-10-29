"""crop_yield/tests/test_crop_yield.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_yield_artifact_predicts():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/random_forest.joblib')
    x=pd.DataFrame([dict(State='Punjab',District='Ludhiana',Crop='Wheat',Season='Rabi',YearStart=2024,Area=1000)])
    assert p.predict(x).shape==(1,)
