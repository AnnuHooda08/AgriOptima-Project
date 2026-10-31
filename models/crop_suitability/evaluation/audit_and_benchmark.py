"""Audit crop suitability data and compare classifiers without touching production.

The benchmark groups identical seven-feature profiles before splitting. This keeps
repeated input profiles, including ones with conflicting labels, in one partition.
The final test partition is used only after validation has selected a challenger.
"""

from __future__ import annotations

import json
import hashlib
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from scipy.sparse import triu
from scipy.sparse.csgraph import connected_components
from sklearn.neighbors import NearestNeighbors

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
DATA_PATH = ROOT / "DataSets" / "crop_suitability.csv"
OUT = MODULE / "evaluation" / "data_audit"
FIGURES = OUT / "figures"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"
SEED = 42
GROUPING_SPANS = np.array([300.0, 300.0, 300.0, 70.0, 100.0, 14.0, 2000.0])


def build_candidates() -> dict[str, object]:
    """Return simple, justified baselines; scaling stays inside each pipeline."""
    return {
        "SVM (RBF, current design)": make_pipeline(
            StandardScaler(), SVC(C=1, kernel="rbf", gamma="scale")
        ),
        "Logistic Regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=3000, random_state=SEED)
        ),
        "Decision Tree": DecisionTreeClassifier(random_state=SEED),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=2, n_jobs=-1, random_state=SEED
        ),
        "K-Nearest Neighbors": make_pipeline(
            StandardScaler(), KNeighborsClassifier(n_neighbors=5, weights="distance")
        ),
    }


def _profile_groups(data: pd.DataFrame) -> np.ndarray:
    """Group exact and very-near profiles so close input rows cannot cross splits.

    Divide each feature by its fixed broad input-range span, then group profiles
    within a 0.005 Euclidean radius. Fixed spans avoid fitting a scaler using
    validation or test data.
    """
    range_scaled = data[FEATURES].to_numpy(dtype=float) / GROUPING_SPANS
    neighbors = NearestNeighbors(radius=0.005, metric="euclidean").fit(range_scaled)
    graph = neighbors.radius_neighbors_graph(range_scaled, mode="connectivity")
    _, labels = connected_components(graph, directed=False)
    return labels


def _three_way_group_split(data: pd.DataFrame):
    """Create about 60/20/20 splits without exact or very-near profile overlap."""
    groups = _profile_groups(data)
    test_splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_validation_idx, test_idx = next(
        test_splitter.split(data[FEATURES], data[TARGET], groups)
    )
    train_validation = data.iloc[train_validation_idx]
    train_validation_groups = groups[train_validation_idx]
    validation_splitter = StratifiedGroupKFold(
        n_splits=4, shuffle=True, random_state=SEED + 1
    )
    train_relative, validation_relative = next(
        validation_splitter.split(
            train_validation[FEATURES],
            train_validation[TARGET],
            train_validation_groups,
        )
    )
    train_idx = train_validation_idx[train_relative]
    validation_idx = train_validation_idx[validation_relative]
    train = data.iloc[train_idx]
    validation = data.iloc[validation_idx]
    test = data.iloc[test_idx]
    partitions = {"train": train, "validation": validation, "test": test}
    profile_sets = {
        "train": set(groups[train_idx]),
        "validation": set(groups[validation_idx]),
        "test": set(groups[test_idx]),
    }
    assert not (profile_sets["train"] & profile_sets["validation"])
    assert not (profile_sets["train"] & profile_sets["test"])
    assert not (profile_sets["validation"] & profile_sets["test"])
    return partitions


def _metrics(actual, predicted) -> dict[str, float]:
    """Calculate class-balanced and support-weighted classification measures."""
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_precision": float(
            precision_score(actual, predicted, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(actual, predicted, average="macro", zero_division=0)
        ),
        "macro_f1": float(f1_score(actual, predicted, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(actual, predicted, average="weighted", zero_division=0)
        ),
    }


def _write_json(path: Path, value: object) -> None:
    """Write JSON with stable, readable formatting."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def audit_data(data: pd.DataFrame) -> dict:
    """Create dataset audit tables, descriptive plots, and a factual summary."""
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = data.copy()
    data.columns = [str(column).strip() for column in data.columns]
    missing_columns = sorted(set(FEATURES + [TARGET]) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Dataset lacks required columns: {missing_columns}")

    for column in FEATURES:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data[TARGET] = data[TARGET].astype("string").str.strip()
    numeric = data[FEATURES]
    finite_rows = np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1)
    has_label = data[TARGET].notna() & data[TARGET].ne("")
    valid_rows = finite_rows & has_label.to_numpy()

    class_counts = data[TARGET].value_counts(dropna=False).sort_values(ascending=False)
    class_counts.rename_axis("crop").reset_index(name="records").to_csv(
        OUT / "crop_class_counts.csv", index=False
    )
    numeric.describe(percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]).T.to_csv(
        OUT / "feature_summary.csv"
    )
    numeric.corr().to_csv(OUT / "feature_correlation_matrix.csv")
    data.groupby(TARGET, dropna=False)[FEATURES].agg(["count", "mean", "median", "std", "min", "max"]).to_csv(
        OUT / "feature_summary_by_crop.csv"
    )

    feature_profiles = data[FEATURES].copy()
    profile_groups = data.groupby(FEATURES, dropna=False, sort=False)
    profile_stats = profile_groups[TARGET].agg(
        rows="size", distinct_labels="nunique", labels=lambda values: " | ".join(sorted(map(str, set(values))))
    ).reset_index()
    profile_stats[profile_stats["rows"] > 1].to_csv(OUT / "repeated_feature_profiles.csv", index=False)
    profile_stats[profile_stats["distinct_labels"] > 1].to_csv(
        OUT / "conflicting_feature_profiles.csv", index=False
    )
    conflict_rows = int(
        profile_stats.loc[profile_stats["distinct_labels"] > 1, "rows"].sum()
    )

    # Close distinct profiles are reported separately from exact duplicates.
    close_groups = _profile_groups(data)
    close_group_sizes = pd.Series(close_groups).value_counts()
    range_scaled = data[FEATURES].to_numpy(dtype=float) / GROUPING_SPANS
    pair_graph = NearestNeighbors(radius=0.005, metric="euclidean").fit(
        range_scaled
    ).radius_neighbors_graph(range_scaled, mode="distance")
    pair_graph = triu(pair_graph, k=1).tocoo()
    near_pairs = pd.DataFrame({
        "source_row_a": pair_graph.row + 2,
        "source_row_b": pair_graph.col + 2,
        "standardized_euclidean_distance": pair_graph.data,
        "crop_a": data[TARGET].iloc[pair_graph.row].to_numpy(),
        "crop_b": data[TARGET].iloc[pair_graph.col].to_numpy(),
    })
    near_pairs["labels_differ"] = near_pairs["crop_a"] != near_pairs["crop_b"]
    near_pairs.to_csv(OUT / "near_feature_profile_pairs.csv", index=False)
    close_group_crop_counts = data.assign(_group=close_groups).groupby("_group")[TARGET].nunique()

    # Broad physical checks are screening flags, not a reason to delete rows.
    plausible = {
        "N": (0, 300), "P": (0, 300), "K": (0, 300),
        "temperature": (-10, 60), "humidity": (0, 100), "ph": (0, 14), "rainfall": (0, 2000),
    }
    broad_flags = pd.DataFrame(index=data.index)
    for column, (low, high) in plausible.items():
        broad_flags[f"{column}_outside_broad_range"] = (data[column] < low) | (data[column] > high)
    broad_flags["non_finite_or_missing_feature"] = ~finite_rows
    broad_flags["missing_crop_label"] = ~has_label
    iqr_flags = pd.DataFrame(index=data.index)
    # IQR flags identify unusual values within this file; they are not errors by themselves.
    for column in FEATURES:
        q1, q3 = numeric[column].quantile([0.25, 0.75])
        spread = q3 - q1
        iqr_flags[f"{column}_outside_1_5_iqr"] = (numeric[column] < q1 - 1.5 * spread) | (
            numeric[column] > q3 + 1.5 * spread
        )
    flags = pd.concat([broad_flags, iqr_flags], axis=1)
    flagged = flags.any(axis=1)
    audit_rows = data.loc[flagged, FEATURES + [TARGET]].copy()
    audit_rows.insert(0, "source_row_number_after_header", audit_rows.index + 2)
    audit_rows = pd.concat([audit_rows, flags.loc[flagged]], axis=1)
    audit_rows.to_csv(OUT / "suspicious_and_outlier_screen.csv", index=False)

    counts = class_counts.drop(index=pd.NA, errors="ignore")
    min_count = int(counts.min()) if len(counts) else 0
    max_count = int(counts.max()) if len(counts) else 0
    summary = {
        "source_path": str(DATA_PATH.relative_to(ROOT)),
        "rows": int(len(data)),
        "columns": list(data.columns),
        "features": FEATURES,
        "target": TARGET,
        "class_count": int(data[TARGET].nunique(dropna=True)),
        "missing_by_column": {
            str(key): int(value) for key, value in data.isna().sum().items()
        },
        "exact_duplicate_rows": int(data.duplicated().sum()),
        "exact_duplicate_feature_vectors": int(data.duplicated(FEATURES).sum()),
        "unique_feature_profiles": int(profile_stats.shape[0]),
        "conflicting_feature_profiles": int((profile_stats["distinct_labels"] > 1).sum()),
        "rows_in_conflicting_profiles": conflict_rows,
        "near_profile_distance_rule": "connected components at Euclidean distance <= 0.005 after dividing by fixed broad input-range spans",
        "near_profile_connected_groups": int(len(close_group_sizes)),
        "near_profile_non_singleton_groups": int((close_group_sizes > 1).sum()),
        "near_profile_largest_group_size": int(close_group_sizes.max()),
        "near_profile_groups_with_conflicting_labels": int((close_group_crop_counts > 1).sum()),
        "near_profile_pairs_with_different_labels": int(near_pairs["labels_differ"].sum()),
        "valid_finite_feature_and_label_rows": int(valid_rows.sum()),
        "invalid_feature_or_label_rows": int((~valid_rows).sum()),
        "broad_physical_range_or_missing_flags": int(broad_flags.any(axis=1).sum()),
        "statistical_iqr_flags_not_automatically_removed": int(iqr_flags.any(axis=1).sum()),
        "class_count_min": min_count,
        "class_count_max": max_count,
        "class_imbalance_ratio_max_over_min": float(max_count / min_count) if min_count else None,
        "feature_describe": json.loads(numeric.describe().to_json()),
    }
    _write_json(OUT / "dataset_audit_summary.json", summary)

    fig, ax = plt.subplots(figsize=(12, 7))
    class_counts.sort_values().plot(kind="barh", ax=ax, color="#4f8b57")
    ax.set(title="Crop records in the source dataset", xlabel="Rows", ylabel="Crop label")
    fig.tight_layout()
    fig.savefig(FIGURES / "crop_class_counts.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 4, figsize=(15, 8))
    for ax, column in zip(axes.flat, FEATURES):
        ax.hist(data[column], bins=30, color="#4386a8", edgecolor="white")
        ax.set_title(column)
    axes.flat[-1].axis("off")
    fig.suptitle("Distribution of the seven input features", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "feature_distributions.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 7))
    correlations = numeric.corr()
    heatmap = ax.imshow(correlations, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(FEATURES)), FEATURES, rotation=35, ha="right")
    ax.set_yticks(range(len(FEATURES)), FEATURES)
    for row in range(len(FEATURES)):
        for column in range(len(FEATURES)):
            ax.text(column, row, f"{correlations.iloc[row, column]:.2f}", ha="center", va="center")
    fig.colorbar(heatmap, ax=ax, label="Pearson correlation")
    ax.set_title("Pearson correlation among input features")
    fig.tight_layout()
    fig.savefig(FIGURES / "feature_correlations.png", dpi=160)
    plt.close(fig)

    medians = data.groupby(TARGET)[FEATURES].median()
    standardized_medians = (medians - numeric.mean()) / numeric.std(ddof=0)
    fig, ax = plt.subplots(figsize=(11, 9))
    heatmap = ax.imshow(standardized_medians, cmap="coolwarm", vmin=-2.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(FEATURES)), FEATURES, rotation=35, ha="right")
    ax.set_yticks(range(len(medians.index)), medians.index)
    fig.colorbar(heatmap, ax=ax, label="standard deviations from overall mean")
    ax.set_title("Median feature profiles by crop")
    fig.tight_layout()
    fig.savefig(FIGURES / "crop_feature_medians.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(data["N"], data["P"], s=20, alpha=0.45, color="#287ea8")
    ax.set_title("Overall nitrogen and phosphorus distribution")
    fig.tight_layout()
    fig.savefig(FIGURES / "nitrogen_phosphorus_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return summary


def benchmark(data: pd.DataFrame) -> dict:
    """Compare models on validation and report the selected model on test once."""
    OUT.mkdir(parents=True, exist_ok=True)
    partitions = _three_way_group_split(data)
    split_summary = {}
    groups_by_original_index = pd.Series(_profile_groups(data), index=data.index)
    for name, frame in partitions.items():
        split_summary[name] = {
            "rows": int(len(frame)),
            "unique_profile_groups": int(groups_by_original_index.loc[frame.index].nunique()),
            "class_counts": {str(k): int(v) for k, v in frame[TARGET].value_counts().items()},
        }
        frame[FEATURES + [TARGET]].to_csv(OUT / f"{name}_partition.csv", index=False)
    _write_json(OUT / "grouped_split_summary.json", split_summary)

    candidates = build_candidates()
    train = partitions["train"]
    validation = partitions["validation"]
    test = partitions["test"]
    fitted = {}
    validation_predictions = {}
    comparison = []
    for name, candidate in candidates.items():
        model = clone(candidate).fit(train[FEATURES], train[TARGET])
        fitted[name] = model
        train_pred = model.predict(train[FEATURES])
        validation_pred = model.predict(validation[FEATURES])
        validation_predictions[name] = validation_pred
        validation_report = classification_report(
            validation[TARGET], validation_pred, output_dict=True, zero_division=0
        )
        pd.DataFrame(validation_report).T.to_csv(
            OUT / f"per_class_validation_{_safe_name(name)}.csv"
        )
        labels_for_matrix = sorted(data[TARGET].unique())
        pd.DataFrame(
            confusion_matrix(validation[TARGET], validation_pred, labels=labels_for_matrix),
            index=labels_for_matrix,
            columns=labels_for_matrix,
        ).to_csv(OUT / f"confusion_matrix_validation_{_safe_name(name)}.csv")
        comparison.append({
            "model": name,
            "train_rows": len(train),
            "validation_rows": len(validation),
            "train_metrics": _metrics(train[TARGET], train_pred),
            "validation_metrics": _metrics(validation[TARGET], validation_pred),
        })
    comparison.sort(key=lambda row: row["validation_metrics"]["macro_f1"], reverse=True)
    pd.json_normalize(comparison).to_csv(OUT / "model_comparison_validation.csv", index=False)
    _write_json(OUT / "model_comparison_validation.json", comparison)

    importance_rows = []
    for model_name in [comparison[0]["model"], "SVM (RBF, current design)"]:
        importance = permutation_importance(
            fitted[model_name],
            validation[FEATURES],
            validation[TARGET],
            scoring="f1_macro",
            n_repeats=20,
            random_state=SEED,
            n_jobs=-1,
        )
        importance_rows.extend(
            {
                "model": model_name,
                "feature": feature,
                "mean_macro_f1_drop_after_permutation": float(mean),
                "standard_deviation": float(std),
            }
            for feature, mean, std in zip(FEATURES, importance.importances_mean, importance.importances_std)
        )
    pd.DataFrame(importance_rows).to_csv(OUT / "validation_permutation_importance.csv", index=False)

    metric_names = ["accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_f1"]
    fig, ax = plt.subplots(figsize=(14, 6))
    model_positions = np.arange(len(comparison))
    bar_width = 0.15
    for metric_index, metric_name in enumerate(metric_names):
        scores = [row["validation_metrics"][metric_name] for row in comparison]
        offsets = model_positions + (metric_index - (len(metric_names) - 1) / 2) * bar_width
        ax.bar(offsets, scores, width=bar_width, label=metric_name)
    ax.set_xticks(model_positions, [row["model"] for row in comparison])
    ax.set(title="Grouped validation model comparison", xlabel="Model", ylabel="Score", ylim=(0, 1))
    ax.tick_params(axis="x", rotation=12)
    ax.legend(title="Metric", loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.subplots_adjust(right=0.82, bottom=0.25)
    fig.savefig(FIGURES / "validation_model_comparison.png", dpi=160)
    plt.close(fig)

    # Selection uses validation macro F1, with validation accuracy as a tie-breaker.
    winner_name = max(
        comparison,
        key=lambda row: (row["validation_metrics"]["macro_f1"], row["validation_metrics"]["accuracy"]),
    )["model"]
    winner_model = clone(candidates[winner_name]).fit(
        pd.concat([train[FEATURES], validation[FEATURES]], ignore_index=True),
        pd.concat([train[TARGET], validation[TARGET]], ignore_index=True),
    )
    winner_test_pred = winner_model.predict(test[FEATURES])

    # The retained production algorithm is evaluated as a fixed reference using the
    # same development rows. The already-full-data production artifact is not used.
    production_reference = clone(candidates["SVM (RBF, current design)"]).fit(
        pd.concat([train[FEATURES], validation[FEATURES]], ignore_index=True),
        pd.concat([train[TARGET], validation[TARGET]], ignore_index=True),
    )
    production_test_pred = (
        winner_test_pred
        if winner_name == "SVM (RBF, current design)"
        else production_reference.predict(test[FEATURES])
    )
    test_predictions = {winner_name: winner_test_pred}
    if winner_name != "SVM (RBF, current design)":
        test_predictions["SVM (RBF, current design) reference"] = production_test_pred

    test_results = {}
    for name, predicted in test_predictions.items():
        test_results[name] = {
            "rows": int(len(test)),
            "metrics": _metrics(test[TARGET], predicted),
            "per_class": classification_report(
                test[TARGET], predicted, output_dict=True, zero_division=0
            ),
        }
        labels = sorted(data[TARGET].unique())
        matrix = confusion_matrix(test[TARGET], predicted, labels=labels)
        pd.DataFrame(
            matrix,
            index=labels,
            columns=labels,
        ).to_csv(OUT / f"confusion_matrix_test_{_safe_name(name)}.csv")
        row_totals = matrix.sum(axis=1, keepdims=True)
        normalized_matrix = np.divide(
            matrix, row_totals, out=np.zeros_like(matrix, dtype=float), where=row_totals != 0
        )
        fig, ax = plt.subplots(figsize=(13, 11))
        heatmap = ax.imshow(normalized_matrix, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(labels)), labels, rotation=55, ha="right")
        ax.set_yticks(range(len(labels)), labels)
        fig.colorbar(heatmap, ax=ax, label="fraction of each true crop class")
        ax.set(title=f"Grouped test confusion matrix: {name}", xlabel="Predicted label", ylabel="True label")
        ax.tick_params(axis="x", rotation=55)
        ax.tick_params(axis="y", rotation=0)
        fig.tight_layout()
        fig.savefig(FIGURES / f"confusion_matrix_test_{_safe_name(name)}.png", dpi=160)
        plt.close(fig)
        pd.DataFrame(
            classification_report(test[TARGET], predicted, output_dict=True, zero_division=0)
        ).T.to_csv(OUT / f"per_class_test_{_safe_name(name)}.csv")

    # Chickpea is called out explicitly, but no class is hidden from the CSV reports.
    _write_json(OUT / "final_test_results.json", {
        "selection_rule": "highest validation macro F1; validation accuracy breaks ties",
        "selected_model": winner_name,
        "test_results": test_results,
        "warning": "Test results are for final reporting only and did not select or tune a model.",
    })

    # Preserve the current production artifact and save the selected model separately.
    challenger_path = None
    challenger_artifact_saved = False
    if winner_name != "SVM (RBF, current design)":
        source_sha256 = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
        config_fingerprint = hashlib.sha256(
            f"{source_sha256}|{winner_name}|{SEED}|{GROUPING_SPANS.tolist()}|{winner_model.get_params()}".encode()
        ).hexdigest()[:12]
        challenger_path = MODULE / "artifacts" / (
            f"crop_suitability_grouped_split_challenger_{config_fingerprint}.joblib"
        )
        challenger_path.parent.mkdir(parents=True, exist_ok=True)
        if not challenger_path.exists():
            joblib.dump(winner_model, challenger_path)
            challenger_artifact_saved = True
    metadata = {
        "name": winner_name,
        "selected_by": "validation macro F1, accuracy tie-breaker",
        "training_rows": int(len(train) + len(validation)),
        "feature_columns": FEATURES,
        "test_metrics": test_results[winner_name]["metrics"],
        "source_dataset_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
        "artifact_path": str(challenger_path.relative_to(ROOT)) if challenger_path else None,
        "production_artifact_changed": False,
        "test_data_used_for_selection": False,
        "challenger_artifact_saved_this_run": challenger_artifact_saved,
    }
    _write_json(OUT / "challenger_metadata.json", metadata)
    return {
        "split": split_summary,
        "comparison": comparison,
        "selected_model": winner_name,
        "test_results": {name: {"metrics": result["metrics"], "chickpea": result["per_class"].get("chickpea")} for name, result in test_results.items()},
        "challenger_artifact": str(challenger_path.relative_to(ROOT)) if challenger_path else None,
        "challenger_artifact_saved_this_run": challenger_artifact_saved,
    }


def _safe_name(name: str) -> str:
    """Create portable short report filenames."""
    return "_".join("".join(char.lower() if char.isalnum() else " " for char in name).split())


def main() -> None:
    """Run the data audit first, then the grouped model evaluation."""
    data = pd.read_csv(DATA_PATH)
    audit = audit_data(data)
    benchmark_result = benchmark(data)
    _write_json(OUT / "run_summary.json", {"audit": audit, "benchmark": benchmark_result})
    print(json.dumps(benchmark_result, indent=2))


if __name__ == "__main__":
    warnings.filterwarnings("default", category=UserWarning)
    main()
