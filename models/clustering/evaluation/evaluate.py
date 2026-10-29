"""Select k on training locations and measure cluster separation on held-out locations."""
from pathlib import Path
import json
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import silhouette_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

MODULE = Path(__file__).resolve().parents[1]
FEATURES = [
    "depth_top_cm", "depth_bottom_cm", "ph_h2o", "organic_carbon_g_kg",
    "total_nitrogen_g_kg", "sand_pct", "silt_pct", "clay_pct",
    "bulk_density_g_cm3", "cec_cmol_kg", "coarse_fragments_vol_pct",
]

def evaluate():
    # Keep all depth samples from one coordinate pair in the same split.
    data = pd.read_csv(MODULE / "data" / "processed" / "soil_sample.csv")
    groups = data["latitude"].round(5).astype(str) + "|" + data["longitude"].round(5).astype(str)
    train_idx, test_idx = next(GroupShuffleSplit(
        n_splits=1, test_size=0.2, random_state=42
    ).split(data, groups=groups))
    train, test = data.iloc[train_idx], data.iloc[test_idx]
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_x = scaler.fit_transform(imputer.fit_transform(train[FEATURES]))
    test_x = scaler.transform(imputer.transform(test[FEATURES]))

    # Choose k only with training locations, then score the selected clusters on held-out points.
    selection = {}
    selected_k = None
    selected_score = -float("inf")
    for k in [2, 3, 4, 5]:
        model = KMeans(n_clusters=k, n_init=10, random_state=42).fit(train_x)
        score = silhouette_score(
            train_x, model.labels_, sample_size=min(2000, len(train_x)), random_state=42
        )
        selection[str(k)] = float(score)
        if score > selected_score:
            selected_k, selected_score = k, score
    final = KMeans(n_clusters=selected_k, n_init=10, random_state=42).fit(train_x)
    labels = final.predict(test_x)
    if len(set(labels)) < 2:
        raise ValueError("The held-out soil sample formed fewer than two predicted clusters.")
    test_sample = min(2000, len(test_x))
    score = float(silhouette_score(
        test_x, labels, sample_size=test_sample, random_state=42
    ))
    result = {
        "split": "coordinate-group holdout; random_state=42",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "selected_k": int(selected_k),
        "training_silhouette_by_k": selection,
        "holdout_silhouette": score,
        "silhouette_sample_rows": int(test_sample),
        "interpretation": "geometric separation only; clusters are not crop recommendations",
    }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate()
