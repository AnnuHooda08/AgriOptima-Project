"""crop_suitability/tests/test_crop_suitability.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_artifact_predicts_label():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/crop_suitability_pipeline.pkl')
    row=pd.DataFrame([dict(N=90,P=42,K=43,temperature=20,humidity=80,ph=6.5,rainfall=200)])
    assert isinstance(p.predict(row)[0],str)
