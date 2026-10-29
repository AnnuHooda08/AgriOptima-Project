"""clustering/tests/test_clustering.py: model workflow entry point; see its folder README for usage."""
from pathlib import Path
import joblib,pandas as pd
def test_cluster_artifact_predicts():
    p=joblib.load(Path(__file__).resolve().parents[1]/'artifacts/soil_kmeans.joblib')
    x=pd.DataFrame([{k:1.0 for k in p['features']}])
    assert p['model'].predict(x).shape==(1,)
