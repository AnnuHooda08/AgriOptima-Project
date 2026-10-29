"""Select and fit the final K-means soil-profile clustering artifact."""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

MODULE = Path(__file__).resolve().parents[1]
FEATURES = [
    "depth_top_cm", "depth_bottom_cm", "ph_h2o", "organic_carbon_g_kg",
    "total_nitrogen_g_kg", "sand_pct", "silt_pct", "clay_pct",
    "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct",
]

def build_model(k):
    # Impute and scale because the numeric features have different measurement units.
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("cluster", KMeans(n_clusters=k, n_init=10, random_state=42)),
    ])

def train():
    # Silhouette is used as an unsupervised separation guide, not as crop-quality proof.
    data = pd.read_csv(MODULE / "data" / "processed" / "soil_sample.csv")
    scores = {}
    best = None
    sample = data[FEATURES].sample(min(5000, len(data)), random_state=42)
    for k in [2, 3, 4, 5]:
        model = build_model(k).fit(sample)
        scores[str(k)] = float(silhouette_score(
            model[:-1].transform(sample), model[-1].labels_,
            sample_size=min(2000, len(sample)), random_state=42
        ))
        if best is None or scores[str(k)] > scores[str(best[0])]:
            best = (k, model)
    # Refit the selected k on all sampled records for final inference.
    final_model = build_model(best[0]).fit(data[FEATURES])
    artifact = MODULE / "artifacts" / "soil_kmeans.joblib"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "features": FEATURES, "k": best[0]}, artifact)
    report = MODULE / "training" / "selection_scores.json"
    report.write_text(json.dumps({"selection_scores": scores, "selected_k": best[0]}, indent=2) + "\n")
    print(f"Selected k={best[0]} from {scores}; saved {artifact}")
    return final_model

if __name__ == "__main__":
    train()
