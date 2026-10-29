"""Evaluate the SVC on a fixed, stratified holdout and save honest metrics."""
from pathlib import Path
import json
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET, prepare
from train import build_model

def evaluate():
    # Stratification keeps rare crop labels represented in both partitions.
    data = prepare()
    train_x, test_x, train_y, test_y = train_test_split(
        data[FEATURES], data[TARGET], test_size=0.2, random_state=42, stratify=data[TARGET]
    )
    model = build_model().fit(train_x, train_y)
    predicted = model.predict(test_x)
    result = {
        "split": "stratified 80/20; random_state=42",
        "test_rows": int(len(test_y)),
        "accuracy": float(accuracy_score(test_y, predicted)),
        "macro_f1": float(f1_score(test_y, predicted, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(test_y, predicted, average="weighted", zero_division=0)),
        "macro_precision": float(precision_score(test_y, predicted, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(test_y, predicted, average="macro", zero_division=0)),
    }
    output = MODULE / "evaluation" / "holdout_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(classification_report(test_y, predicted, zero_division=0))
    return result

if __name__ == "__main__":
    evaluate()
