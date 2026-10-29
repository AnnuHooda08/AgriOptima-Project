"""anomaly_detection/tests/test_anomaly_detection.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_anomaly_model_scores():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/soil_isolation_forest.joblib')
    assert p['model'].decision_function(pd.DataFrame([{k:1.0 for k in p['features']}])).shape==(1,)
