"""Audit yield distribution shift, crop mix, source extremes, and validation groups."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parents[1]
RAW_FILE = ROOT / "DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv"
OUT = MODULE / "evaluation" / "data_audit"
PLOTS = OUT / "plots"
sys.path.insert(0, str(MODULE / "preprocessing"))
sys.path.insert(0, str(MODULE / "training"))
from prepare_data import FEATURES, TARGET
from train_compare_models import build_candidate, candidates

# The five named periods intentionally overlap: 2006-08 and 2009-11 are
# robustness windows contained inside the broader training period.
PERIODS = {
    "Training 1997-2011": (1997, 2011),
    "Validation 2012-2014": (2012, 2014),
    "Test 2015-2019": (2015, 2019),
    "Earlier validation 2006-2008": (2006, 2008),
    "Earlier validation 2009-2011": (2009, 2011),
}
EARLY_VALIDATION_WINDOWS = [
    ("2006-2008", 2006, 2008),
    ("2009-2011", 2009, 2011),
    ("2012-2014", 2012, 2014),
]


def load_accepted_source():
    """Recreate accepted rows while retaining their original CSV line numbers."""
    source = pd.read_csv(RAW_FILE, low_memory=False)
    source.columns = [str(column).strip() for column in source.columns]
    source["source_csv_row"] = np.arange(len(source)) + 2
    original_columns = [column for column in source.columns if column != "source_csv_row"]
    source = source.drop_duplicates(subset=original_columns).copy()
    for column in ["State", "District", "Crop", "Season", "Area Units", "Production Units"]:
        source[column] = source[column].astype("string").str.strip()
    for column in ["Area", "Production", "Yield"]:
        source[column] = pd.to_numeric(source[column], errors="coerce")
    source["YearStart"] = pd.to_numeric(
        source["Year"].astype("string").str.extract(r"((?:19|20)\d{2})", expand=False),
        errors="coerce",
    )
    valid_area_unit = source["Area Units"].str.casefold().isin(["hectare", "hectares", "ha"])
    valid_production_unit = source["Production Units"].str.casefold().isin(
        ["tonne", "tonnes", "metric tonne", "metric tonnes", "metric ton", "metric tons"]
    )
    valid = (
        source[["State", "District", "Crop", "Season", "YearStart", "Area", "Yield"]]
        .notna().all(axis=1)
        & source["Area"].gt(0)
        & source["Yield"].gt(0)
        & valid_area_unit
        & valid_production_unit
    )
    clean = source.loc[valid].copy()
    expected_rows = 9882
    if len(clean) != expected_rows:
        raise ValueError(f"Audit cleaning produced {len(clean)} rows; expected {expected_rows}.")
    clean["YearStart"] = clean["YearStart"].astype(int)
    return source, clean


def period_rows(data):
    """Return named year-period subsets without changing source data."""
    return {
        label: data[data["YearStart"].between(first, last)].copy()
        for label, (first, last) in PERIODS.items()
    }


def target_distribution(period_data):
    """Calculate requested descriptive yield statistics for each period."""
    rows = []
    percentiles = [0.01, 0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    for label, frame in period_data.items():
        row = {
            "period": label,
            "records": len(frame),
            "mean_t_ha": frame[TARGET].mean(),
            "median_t_ha": frame[TARGET].median(),
            "std_t_ha": frame[TARGET].std(ddof=1),
            "min_t_ha": frame[TARGET].min(),
            "max_t_ha": frame[TARGET].max(),
        }
        for quantile in percentiles:
            row[f"p{int(quantile * 100):02d}_t_ha"] = frame[TARGET].quantile(quantile)
        rows.append(row)
    return pd.DataFrame(rows)


def crop_composition(period_data):
    """Write period-by-crop counts and proportions for all recorded crop classes."""
    counts = []
    for label, frame in period_data.items():
        group = frame["Crop"].value_counts()
        for crop, count in group.items():
            counts.append({
                "period": label,
                "crop": crop,
                "records": int(count),
                "period_records": int(len(frame)),
                "proportion": float(count / len(frame)),
            })
    return pd.DataFrame(counts)


def crop_yield_by_period(period_data):
    """Describe within-crop yield shifts, alongside crop record composition."""
    rows = []
    for period, frame in period_data.items():
        grouped = frame.groupby("Crop")[TARGET].agg(
            records="size", mean_t_ha="mean", median_t_ha="median", std_t_ha="std",
            p95_t_ha=lambda values: values.quantile(.95),
        ).reset_index()
        grouped.insert(0, "period", period)
        rows.extend(grouped.to_dict(orient="records"))
    return pd.DataFrame(rows)


def unseen_crop_support(data):
    """Count categories/combos absent in the 1997-2011 training period."""
    training = data[data["YearStart"].between(1997, 2011)]
    seen_crops = set(training["Crop"])
    seen_combinations = set(zip(training["Crop"], training["Season"]))
    summary = {}
    for period, start, end in [
        ("validation_2012_2014", 2012, 2014),
        ("test_2015_2019", 2015, 2019),
    ]:
        frame = data[data["YearStart"].between(start, end)]
        unseen_crop_mask = ~frame["Crop"].isin(seen_crops)
        combos = list(zip(frame["Crop"], frame["Season"]))
        unseen_combo_mask = [combo not in seen_combinations for combo in combos]
        summary[period] = {
            "unseen_crop_labels": sorted(set(frame.loc[unseen_crop_mask, "Crop"])),
            "records_with_unseen_crop_label": int(unseen_crop_mask.sum()),
            "unseen_crop_season_combinations": sorted(
                [list(combo) for combo in set(combos) if combo not in seen_combinations]
            ),
            "records_with_unseen_crop_season_combination": int(sum(unseen_combo_mask)),
        }
    return summary


def ambiguous_district_labels(data):
    """Flag very short district labels for provenance review without discarding rows."""
    short = data["District"].str.strip().str.len().lt(3)
    summary = data.loc[short].groupby(["State", "District"]).agg(
        records=("District", "size"),
        first_year=("YearStart", "min"),
        last_year=("YearStart", "max"),
        crops=("Crop", "nunique"),
    ).reset_index()
    return summary


def crop_mix_test(data):
    """Test crop-composition association across disjoint train/validation/test groups."""
    main = data[data["YearStart"].between(1997, 2019)].copy()
    main["period"] = pd.cut(
        main["YearStart"],
        bins=[1996, 2011, 2014, 2019],
        labels=["train_1997_2011", "validation_2012_2014", "test_2015_2019"],
    )
    crop_totals = main["Crop"].value_counts()
    rare = set(crop_totals[crop_totals < 50].index)
    main["crop_group"] = main["Crop"].where(~main["Crop"].isin(rare), "Other (crop total < 30)")
    table = pd.crosstab(main["period"], main["crop_group"])
    chi2, p_value, degrees, expected = chi2_contingency(table)
    n = int(table.to_numpy().sum())
    denom = min(table.shape[0] - 1, table.shape[1] - 1)
    cramer_v = float(np.sqrt(chi2 / (n * denom))) if denom else 0.0
    return {
        "comparison": "disjoint train, validation, and test periods",
        "rare_crop_rule": "Crop classes with fewer than 50 total accepted rows pooled as Other for the chi-square test.",
        "periods": list(table.index.astype(str)),
        "crop_groups": list(table.columns.astype(str)),
        "contingency_counts": table.to_dict(orient="index"),
        "chi_square": float(chi2),
        "degrees_of_freedom": int(degrees),
        "p_value": float(p_value),
        "cramers_v": cramer_v,
        "minimum_expected_cell_count": float(expected.min()),
        "interpretation": (
            "Crop composition differs statistically across periods; Cramer's V describes effect size."
            if p_value < 0.05
            else "The test did not find evidence of a crop-composition difference at alpha 0.05."
        ),
    }


def audit_extremes(raw, clean, count=100):
    """Trace the largest accepted yields to raw CSV rows and check arithmetic/units."""
    top = clean.nlargest(count, TARGET).copy()
    top["production_area_ratio_t_ha"] = top["Production"] / top["Area"]
    top["tonnes_per_hectare_match"] = np.isclose(
        top["production_area_ratio_t_ha"], top[TARGET], rtol=1e-6, atol=1e-8
    )
    valid_tonne = top["Production Units"].str.casefold().isin(
        ["tonne", "tonnes", "metric tonne", "metric tonnes", "metric ton", "metric tons"]
    )
    valid_hectare = top["Area Units"].str.casefold().isin(["hectare", "hectares", "ha"])
    top["unit_consistency"] = np.where(
        valid_tonne & valid_hectare,
        "tonnes / hectares",
        "unit mismatch or unrecognized",
    )

    # Crop-specific IQR screens are flags for review, never automatic exclusions.
    fences = clean.groupby("Crop")[TARGET].agg(
        q1=lambda values: values.quantile(.25),
        q3=lambda values: values.quantile(.75),
    )
    fences["upper_fence"] = fences["q3"] + 1.5 * (fences["q3"] - fences["q1"])
    top["crop_iqr_upper_fence_t_ha"] = top["Crop"].map(fences["upper_fence"])
    top["crop_iqr_flag"] = top[TARGET] > top["crop_iqr_upper_fence_t_ha"]
    top["source_check_class"] = "Arithmetic/unit consistent; agricultural value not independently verified"
    mismatch = ~(valid_tonne & valid_hectare & top["tonnes_per_hectare_match"])
    suspicious = mismatch | (top[TARGET].ge(100) & top["Area"].le(2))
    top.loc[mismatch, "source_check_class"] = "Suspicious: unit or production/area/yield mismatch"
    top.loc[suspicious & ~mismatch, "source_check_class"] = (
        "Suspicious screening flag: extreme yield with very small area; arithmetic still matches"
    )
    needs_followup = top["crop_iqr_flag"] & ~suspicious
    top.loc[needs_followup, "source_check_class"] = (
        "Requires source-owner follow-up: crop-specific IQR outlier, arithmetic still matches"
    )
    fields = [
        "source_csv_row", "State", "District", "Crop", "Season", "Year",
        "Area", "Area Units", "Production", "Production Units", "Yield",
        "production_area_ratio_t_ha", "tonnes_per_hectare_match", "unit_consistency",
        "crop_iqr_upper_fence_t_ha", "crop_iqr_flag", "source_check_class",
    ]
    audit = top[fields].sort_values(TARGET, ascending=False)
    audit.to_csv(OUT / "largest_source_records_audit.csv", index=False)
    for label, mask in [
        ("arithmetic_unit_consistent_top100", audit["tonnes_per_hectare_match"] & audit["unit_consistency"].eq("tonnes / hectares")),
        ("suspicious_top_records", audit["source_check_class"].str.startswith("Suspicious")),
        ("requires_source_followup_top_records", audit["source_check_class"].str.startswith("Requires")),
        ("arithmetic_checked_not_iqr_flagged", audit["source_check_class"].str.startswith("Arithmetic")),
    ]:
        audit.loc[mask].to_csv(OUT / f"{label}.csv", index=False)
    return audit


def group_performance(data):
    """Measure fixed candidate errors on historical validation windows only."""
    rows = []
    group_tables = {}
    for period, start, end in EARLY_VALIDATION_WINDOWS:
        train_mask = data["YearStart"] < start
        valid_mask = data["YearStart"].between(start, end)
        # The crop-season tree mirrors the challenger; all-six RF mirrors production inputs.
        for model_name, config_name, features in [
            ("Decision Tree", "Crop + Season", ["Crop", "Season"]),
            ("Random Forest", "All six production inputs", FEATURES),
        ]:
            estimator = candidates()[model_name]
            pipeline = build_candidate(estimator, features=features)
            pipeline.fit(data.loc[train_mask, features], data.loc[train_mask, TARGET])
            frame = data.loc[valid_mask, ["State", "District", "Crop", "Season", "YearStart", TARGET]].copy()
            frame["prediction"] = pipeline.predict(data.loc[valid_mask, features])
            frame["residual"] = frame[TARGET] - frame["prediction"]
            frame["absolute_error"] = frame["residual"].abs()
            frame["validation_period"] = period
            frame["model"] = model_name
            frame["feature_config"] = config_name
            rows.append(frame)
            if period == "2012-2014":
                group_tables[(model_name, config_name)] = frame.copy()
    predictions = pd.concat(rows, ignore_index=True)
    predictions.to_csv(OUT / "historical_validation_predictions.csv", index=False)

    # Report full metrics only where there are at least 30 validation rows.
    reliable_rows, low_count_rows = [], []
    for (model_name, config_name), frame in group_tables.items():
        for column in ["State", "District", "Crop", "Season"]:
            for group, part in frame.groupby(column):
                record = {
                    "model": model_name,
                    "feature_config": config_name,
                    "group_type": column,
                    "group": group,
                    "records": int(len(part)),
                }
                if len(part) >= 30:
                    record.update({
                        "mae_t_ha": float(part["absolute_error"].mean()),
                        "rmse_t_ha": float(np.sqrt(np.mean(part["residual"] ** 2))),
                        "mean_residual_t_ha": float(part["residual"].mean()),
                    })
                    reliable_rows.append(record)
                else:
                    # Low-count group rows contain counts only, no misleading metrics.
                    low_count_rows.append(record)
    pd.DataFrame(reliable_rows).to_csv(OUT / "validation_group_metrics_n30plus.csv", index=False)
    pd.DataFrame(low_count_rows).to_csv(OUT / "validation_groups_low_count.csv", index=False)
    return predictions, reliable_rows, low_count_rows


def make_plots(period_data, composition):
    """Create readable period-distribution and crop-share visualizations."""
    sns.set_theme(style="whitegrid")
    colors = sns.color_palette("colorblind", n_colors=len(period_data))
    labels = list(period_data)

    fig, ax = plt.subplots(figsize=(11, 6))
    for label, color in zip(labels, colors):
        values = period_data[label][TARGET].sort_values().to_numpy()
        cumulative = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, cumulative, label=f"{label} (n={len(values):,})", color=color)
    ax.set_xscale("symlog", linthresh=1)
    ax.set(title="Yield distribution by period (symmetric log x-axis)",
           xlabel="Yield (tonnes/hectare; symlog scale)", ylabel="Cumulative share")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "yield_ecdf_by_period.png", dpi=170)
    plt.close(fig)

    # Log1p display makes the long right tail visible while retaining zero reference.
    fig, ax = plt.subplots(figsize=(11, 6))
    stacked = [period_data[label][TARGET] for label in labels]
    ax.boxplot(stacked, tick_labels=[f"{label}\n(n={len(values):,})" for label, values in zip(labels, stacked)],
               showfliers=False)
    ax.set_yscale("symlog", linthresh=1)
    ax.set(title="Yield median and interquartile range by period (outlier markers hidden)",
           ylabel="Yield (tonnes/hectare; symlog scale)")
    fig.tight_layout()
    fig.savefig(PLOTS / "yield_boxplot_by_period.png", dpi=170)
    plt.close(fig)

    top_crops = composition[composition["period"].eq("Training 1997-2011")].nlargest(10, "records")["crop"].tolist()
    grouped = composition.copy()
    grouped["crop_group"] = grouped["crop"].where(grouped["crop"].isin(top_crops), "Other crops")
    shares = grouped.pivot_table(index="period", columns="crop_group", values="proportion", aggfunc="sum", fill_value=0)
    shares = shares.reindex(labels)
    fig, ax = plt.subplots(figsize=(12, 6))
    shares.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    ax.set(title="Crop composition by period (top training crops plus other crops)",
           xlabel="Period", ylabel="Share of accepted records")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Crop", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "crop_composition_by_period.png", dpi=170)
    plt.close(fig)

    sugar = composition[composition["crop"].str.casefold().eq("sugarcane")]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(sugar["period"], 100 * sugar["proportion"], color="#b36b00")
    ax.set(title="Sugarcane share of accepted rows by period",
           xlabel="Period", ylabel="Share of rows (%)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(PLOTS / "sugarcane_share_by_period.png", dpi=170)
    plt.close(fig)


def run_audit():
    """Create descriptive reports; final test is never used for model selection."""
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    raw, clean = load_accepted_source()
    periods = period_rows(clean)
    distribution = target_distribution(periods)
    distribution.to_csv(OUT / "target_distribution_by_period.csv", index=False)

    composition = crop_composition(periods)
    composition.to_csv(OUT / "crop_composition_by_period.csv", index=False)
    yield_by_crop = crop_yield_by_period(periods)
    yield_by_crop.to_csv(OUT / "yield_by_crop_and_period.csv", index=False)
    counts = composition.pivot(index="crop", columns="period", values="records").fillna(0).astype(int)
    shares = composition.pivot(index="crop", columns="period", values="proportion").fillna(0)
    counts.to_csv(OUT / "crop_counts_by_period_wide.csv")
    shares.to_csv(OUT / "crop_shares_by_period_wide.csv")

    composition_test = crop_mix_test(clean)
    (OUT / "crop_composition_chi_square.json").write_text(
        json.dumps(composition_test, indent=2) + "\n"
    )
    extremes = audit_extremes(raw, clean)
    short_districts = ambiguous_district_labels(clean)
    short_districts.to_csv(OUT / "ambiguous_district_labels.csv", index=False)
    # Show how the single 2,150 t/ha record affects moments; retain all records.
    train_period = periods["Training 1997-2011"][TARGET]
    early_window = periods["Earlier validation 2006-2008"][TARGET]
    max_training = float(train_period.max())
    extreme_influence = {
        "highest_training_yield_t_ha": max_training,
        "training_mean_all_rows": float(train_period.mean()),
        "training_std_all_rows": float(train_period.std(ddof=1)),
        "training_mean_without_one_max_for_sensitivity_only": float(train_period[train_period.ne(max_training)].mean()),
        "training_std_without_one_max_for_sensitivity_only": float(train_period[train_period.ne(max_training)].std(ddof=1)),
        "2006_2008_mean_all_rows": float(early_window.mean()),
        "2006_2008_std_all_rows": float(early_window.std(ddof=1)),
        "2006_2008_mean_without_one_max_for_sensitivity_only": float(early_window[early_window.ne(max_training)].mean()),
        "2006_2008_std_without_one_max_for_sensitivity_only": float(early_window[early_window.ne(max_training)].std(ddof=1)),
        "note": "The record is not removed from any dataset or model; this is a descriptive influence check only.",
    }
    unseen = unseen_crop_support(clean)
    predictions, reliable, low_count = group_performance(clean)
    make_plots(periods, composition)

    sugar_rows = composition[composition["crop"].str.casefold().eq("sugarcane")]
    summary = {
        "accepted_rows": int(len(clean)),
        "periods": {label: int(len(frame)) for label, frame in periods.items()},
        "target_distribution": distribution.to_dict(orient="records"),
        "crop_composition_test": composition_test,
        "unseen_validation_test_crop_support": unseen,
        "extreme_influence_sensitivity": extreme_influence,
        "sugarcane_period_rows": sugar_rows.to_dict(orient="records"),
        "extreme_records_reviewed": int(len(extremes)),
        "short_district_labels": short_districts.to_dict(orient="records"),
        "extreme_source_class_counts": extremes["source_check_class"].value_counts().to_dict(),
        "validation_group_metrics_minimum_n": 30,
        "validation_metrics_do_not_cover_final_test": True,
        "artifact_files_written": [],
    }
    (OUT / "data_generalization_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(distribution.to_string(index=False))
    print("\nSugarcane share:")
    print(sugar_rows[["period", "records", "proportion"]].to_string(index=False))
    print("\nCrop-mix test:")
    print(json.dumps({
        "chi_square": composition_test["chi_square"],
        "degrees_of_freedom": composition_test["degrees_of_freedom"],
        "p_value": composition_test["p_value"],
        "cramers_v": composition_test["cramers_v"],
        "minimum_expected_cell_count": composition_test["minimum_expected_cell_count"],
    }, indent=2))
    print("\nExtreme-record review classes:")
    print(extremes["source_check_class"].value_counts().to_string())
    print(f"Validation group summaries: {len(reliable)} groups with n>=30; {len(low_count)} low-count groups withheld from metrics.")
    print("Final test rows were used only for descriptive distributions; they were not used to tune or select models.")
    return summary


if __name__ == "__main__":
    run_audit()
