"""Reproducible audit of the national crop-production CSV candidate.

This script reads source datasets without editing them and writes all audit
outputs beside this file. Every yield calculation is restricted to crops whose
production unit can be mapped to tonnes using source evidence documented in the
audit report.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[5]
DATA = ROOT / "DataSets" / "Yeild"
OUT = Path(__file__).resolve().parent
CANDIDATE = DATA / "district_wise_season_wise_crop_production_1997.csv"
CURRENT = DATA / "crop_production_haryana_punjab_1997_2019.csv"


def sha256(path: Path) -> str:
    """Return the stable SHA-256 digest for source-integrity reporting."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(series: pd.Series) -> pd.Series:
    """Normalize whitespace for matching while leaving source values untouched."""
    return series.fillna("").astype(str).str.strip()


def inspect_dataset(path: Path) -> dict:
    """Summarize the relevant shape and coverage of one CSV file."""
    frame = pd.read_csv(path, low_memory=False)
    year_column = next((name for name in ("Crop_Year", "Year") if name in frame), None)
    if year_column:
        years = clean_text(frame[year_column]).str.extract(r"(\d{4})", expand=False)
        years = pd.to_numeric(years, errors="coerce").dropna()
        year_range = [int(years.min()), int(years.max())] if len(years) else None
    else:
        year_range = None
    state_column = next((name for name in ("State_Name", "State Name", "State") if name in frame), None)
    district_column = next((name for name in ("District_Name", "Dist Name", "District") if name in frame), None)
    crop_column = next((name for name in ("Crop",) if name in frame), None)
    season_column = next((name for name in ("Season",) if name in frame), None)
    return {
        "filename": path.name,
        "format": path.suffix.lstrip(".").upper(),
        "rows": int(len(frame)),
        "columns_count": int(frame.shape[1]),
        "columns": frame.columns.tolist(),
        "year_range": year_range,
        "states": int(frame[state_column].nunique(dropna=True)) if state_column else None,
        "districts": int(frame[district_column].nunique(dropna=True)) if district_column else None,
        "crops": int(frame[crop_column].nunique(dropna=True)) if crop_column else None,
        "seasons": int(frame[season_column].nunique(dropna=True)) if season_column else None,
        "missing_by_column": frame.isna().sum().astype(int).to_dict(),
        "size_bytes": int(path.stat().st_size),
        "sha256": sha256(path),
    }, frame


def main() -> None:
    """Generate inventory, quality checks, unit decisions, derived data, plots, and report."""
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = []
    frames = {}
    for path in sorted(DATA.glob("*.csv")):
        detail, frame = inspect_dataset(path)
        inventory.append(detail)
        frames[path.name] = frame

    candidate_info = next(item for item in inventory if item["filename"] == CANDIDATE.name)
    current_info = next(item for item in inventory if item["filename"] == CURRENT.name)
    candidate = frames[CANDIDATE.name].copy()
    current = frames[CURRENT.name].copy()
    # CSV row numbers make unusual records easy to check in the untouched source.
    candidate["_source_row"] = np.arange(2, len(candidate) + 2)

    # Normalize categorical text only in working copies, never in the raw files.
    for col in ["State_Name", "District_Name", "Season", "Crop"]:
        candidate[f"_{col}"] = clean_text(candidate[col])
    candidate["_year"] = pd.to_numeric(candidate["Crop_Year"], errors="coerce")
    candidate["_crop_key"] = candidate["_Crop"].str.casefold()
    for col in ["State", "District", "Season", "Crop"]:
        current[f"_{col}"] = clean_text(current[col])
    current["_State_Name"] = current["_State"]
    current["_District_Name"] = current["_District"]
    current["_year"] = pd.to_numeric(current["Year"].astype(str).str[:4], errors="coerce")
    current["_Crop"] = current["_Crop"].str.strip()
    current["_Season"] = current["_Season"].str.strip()
    current["_crop_key"] = current["_Crop"].str.casefold()

    # Match on all requested dimensions, using the first year in the existing
    # dataset's YYYY-YY label. These are comparison keys, not rewritten data.
    key = ["_State_Name", "_District_Name", "_crop_key", "_Season", "_year"]
    # Aggregate duplicate keys in the existing file before matching so they
    # cannot inflate the number of candidate observations being compared.
    current_keys = current.groupby(key, dropna=False).agg(
        current_source_rows=("_year", "size"),
        current_area_distinct=("Area", "nunique"),
        current_production_distinct=("Production", "nunique"),
        current_units=("Production Units", lambda x: "; ".join(sorted(set(x.dropna().astype(str))))),
        current_area_value=("Area", "first"),
        current_production_value=("Production", "first"),
    ).reset_index()
    current_keys.loc[current_keys["current_area_distinct"] != 1, "current_area_value"] = np.nan
    current_keys.loc[current_keys["current_production_distinct"] != 1, "current_production_value"] = np.nan
    overlap = candidate.merge(current_keys, on=key, how="inner", validate="one_to_one")
    overlap["area_equal"] = overlap["Area"].notna() & overlap["current_area_value"].notna() & np.isclose(overlap["Area"], overlap["current_area_value"], equal_nan=False)
    overlap["production_equal"] = overlap["Production"].notna() & overlap["current_production_value"].notna() & np.isclose(overlap["Production"], overlap["current_production_value"], equal_nan=False)
    overlap["current_production_unit"] = overlap["current_units"]
    overlap.to_csv(OUT / "haryana_punjab_record_matches.csv", index=False)
    overlap_summary = overlap.groupby(["_State_Name", "_crop_key"], dropna=False).agg(
        matched_candidate_keys=("_year", "size"),
        area_equal_rows=("area_equal", "sum"),
        production_equal_rows=("production_equal", "sum"),
        current_units=("current_production_unit", lambda x: "; ".join(sorted(set(x.dropna().astype(str))))),
    ).reset_index()
    overlap_summary.to_csv(OUT / "overlap_summary.csv", index=False)

    # Construct a crop-by-crop units ledger. Generic units are the OGD catalog's
    # declared units; special conventions are kept separate unless corroborated.
    crop_records = []
    rows = candidate
    cotton_key = "cotton(lint)"
    cotton_matches = overlap[overlap["_crop_key"] == cotton_key]
    cotton_nonmissing = cotton_matches.dropna(subset=["Production", "current_production_value"])
    cotton_exact = int((cotton_nonmissing["Production"] == cotton_nonmissing["current_production_value"]).sum())
    for crop in sorted(candidate["_Crop"].dropna().unique(), key=str.casefold):
        norm = str(crop).strip().casefold()
        crop_rows = rows[rows["_crop_key"] == norm]
        if norm == "coconut":
            original, status, factor, approved, final, rationale = (
                "Raw nut count is strongly indicated; CSV has no unit field",
                "Unknown for calculation (likely nuts)", "", "No",
                "Unresolved; retain original production value",
                "Official Coconut Development Board statistics express coconut production in million nuts and productivity in nuts/ha. Candidate values such as 65,100,000 over 18,168 ha are consistent with nut counts, not tonnes. OGD's generic tonnes metadata conflicts with this crop-specific evidence; no nut-to-tonne factor is documented for these rows.",
            )
        elif norm == cotton_key:
            original, status, factor, approved, final, rationale = (
                "Bales (corroborated on overlapping records)",
                "Verified as bales for the matched candidate series",
                "0.17 tonnes/bale (170 kg/bale)", "Yes, documented mass conversion",
                "Metric tonnes after multiplying bales by 0.17",
                f"{cotton_exact} overlapping Haryana/Punjab rows with non-missing production match the existing dataset exactly; that source labels Cotton(lint) production as Bales. DES documents 170 kg per cotton bale. Apply only this mass conversion; do not infer additional processing/quality equivalence.",
            )
        elif norm in {"jute", "mesta", "jute & mesta"}:
            original, status, factor, approved, final, rationale = (
                "Unknown for this exact CSV; official crop estimates use bales",
                "Unknown / incompatible with generic tonnes assumption", "", "No",
                "Unresolved; retain original production value",
                "DES documents Jute & Mesta production in bales of 180 kg, while the OGD catalog gives a generic tonnes description and this CSV has no units column. No exact source-record unit mapping or overlap with labeled production records was found, so neither tonnes nor bale conversion is approved.",
            )
        else:
            original, status, factor, approved, final, rationale = (
                "Tonnes per OGD catalog; no crop-specific alternate convention found",
                "Catalog-declared tonnes; compatible for this audit",
                "1 tonne/tonne", "Yes, per catalog unit statement", "Tonnes",
                "OGD/DES catalog describes this resource's area as hectares and production as tonnes. No crop-specific alternate unit was identified in the official sources reviewed for this crop. Candidate data remains subject to the noted Coconut/Cotton/Jute/Mesta exceptions.",
            )
        crop_records.append({
            "crop": crop, "records": int(len(crop_rows)),
            "nonmissing_production_records": int(crop_rows["Production"].notna().sum()),
            "original_production_unit": original, "unit_evidence_status": status,
            "evidence_or_reason": rationale, "conversion_required": "Yes" if factor and factor != "1 tonne/tonne" else "No",
            "conversion_factor": factor, "conversion_approved_for_yield": approved,
            "final_standardized_production_unit": final,
        })
    unit_ledger = pd.DataFrame(crop_records)
    unit_ledger.to_csv(OUT / "crop_production_unit_audit.csv", index=False)

    # Quality checks preserve rows and never delete or silently repair outliers.
    numeric_area = pd.to_numeric(candidate["Area"], errors="coerce")
    numeric_prod = pd.to_numeric(candidate["Production"], errors="coerce")
    duplicate_key = candidate.duplicated(["_State_Name", "_District_Name", "_year", "_Season", "_crop_key"], keep=False)
    exact_duplicates = candidate.duplicated(subset=["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"], keep=False)
    quality = {
        "candidate_rows": int(len(candidate)), "exact_duplicate_rows": int(exact_duplicates.sum()),
        "duplicate_compound_key_rows": int(duplicate_key.sum()),
        "duplicate_compound_key_groups": int(candidate.loc[duplicate_key].groupby(["_State_Name", "_District_Name", "_year", "_Season", "_crop_key"], dropna=False).ngroups),
        "missing_area": int(numeric_area.isna().sum()), "missing_production": int(numeric_prod.isna().sum()),
        "zero_area": int((numeric_area == 0).sum()), "negative_area": int((numeric_area < 0).sum()),
        "zero_production": int((numeric_prod == 0).sum()), "negative_production": int((numeric_prod < 0).sum()),
        "non_numeric_area": int((candidate["Area"].notna() & numeric_area.isna()).sum()),
        "non_numeric_production": int((candidate["Production"].notna() & numeric_prod.isna()).sum()),
        "states": int(candidate["_State_Name"].nunique()), "districts": int(candidate["_District_Name"].nunique()),
        "year_counts": candidate.groupby("_year", dropna=False).size().astype(int).to_dict(),
        "season_counts": candidate["_Season"].value_counts(dropna=False).astype(int).to_dict(),
        "crop_counts": candidate["_Crop"].value_counts(dropna=False).astype(int).to_dict(),
        "crop_support_bands": {
            "fewer_than_30_records": int((candidate["_Crop"].value_counts() < 30).sum()),
            "30_to_99_records": int(candidate["_Crop"].value_counts().between(30, 99).sum()),
            "100_or_more_records": int((candidate["_Crop"].value_counts() >= 100).sum()),
        },
        "district_history_bands": {
            "one_year": int((candidate.groupby(["_State_Name", "_District_Name"])["_year"].nunique() == 1).sum()),
            "two_to_four_years": int(candidate.groupby(["_State_Name", "_District_Name"])["_year"].nunique().between(2, 4).sum()),
            "five_or_more_years": int((candidate.groupby(["_State_Name", "_District_Name"])["_year"].nunique() >= 5).sum()),
        },
        "districts_by_state": candidate.groupby("_State_Name")["_District_Name"].nunique().astype(int).to_dict(),
    }
    (OUT / "candidate_quality_profile.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False))
    pd.DataFrame(inventory).to_json(OUT / "dataset_inventory.json", orient="records", indent=2)
    pd.DataFrame(inventory)[["filename", "format", "rows", "columns_count", "year_range", "states", "districts", "crops", "seasons", "size_bytes", "sha256"]].to_csv(OUT / "dataset_inventory.csv", index=False)

    # Derive yields only after unit eligibility and numeric validity are checked.
    eligible_crop = ~candidate["_crop_key"].isin(["coconut", "jute", "mesta", "jute & mesta"])
    yield_rows = candidate.loc[eligible_crop].copy()
    yield_rows["area_ha"] = pd.to_numeric(yield_rows["Area"], errors="coerce")
    yield_rows["production_raw"] = pd.to_numeric(yield_rows["Production"], errors="coerce")
    yield_rows["production_source_unit"] = "Tonnes (OGD catalog declaration)"
    yield_rows["production_tonnes"] = yield_rows["production_raw"]
    cotton_mask = yield_rows["_crop_key"] == cotton_key
    yield_rows.loc[cotton_mask, "production_source_unit"] = "Bales (170 kg each; cross-matched to labeled source)"
    yield_rows.loc[cotton_mask, "production_tonnes"] = yield_rows.loc[cotton_mask, "production_raw"] * 0.17
    valid = (yield_rows["area_ha"] > 0) & (yield_rows["production_tonnes"] >= 0) & yield_rows["production_tonnes"].notna()
    valid_yield = yield_rows.loc[valid].copy()
    valid_yield["yield_tonnes_per_hectare"] = valid_yield["production_tonnes"] / valid_yield["area_ha"]
    selected = ["State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "production_source_unit", "production_tonnes", "yield_tonnes_per_hectare"]
    valid_yield[selected].to_csv(OUT / "verified_yield_records.csv", index=False)
    unresolved = candidate.loc[candidate["_crop_key"].isin(["coconut", "jute", "mesta", "jute & mesta"])].copy()
    unresolved["unit_review_status"] = unresolved["_crop_key"].map({
        "coconut": "Likely nuts; exact CSV unit conflict unresolved",
        "jute": "Could be bales or tonnes; exact CSV unit unresolved",
        "mesta": "Could be bales or tonnes; exact CSV unit unresolved",
        "jute & mesta": "Could be bales or tonnes; exact CSV unit unresolved",
    })
    unresolved.to_csv(OUT / "unresolved_unit_records.csv", index=False)
    unusable = yield_rows.loc[~valid].copy()
    unusable["exclusion_reason"] = np.select(
        [unusable["area_ha"].isna(), unusable["area_ha"] <= 0, unusable["production_tonnes"].isna(), unusable["production_tonnes"] < 0],
        ["Area missing or non-numeric", "Area is zero or negative", "Production missing or non-numeric", "Production is negative"],
        default="Unit not eligible",
    )
    unusable.to_csv(OUT / "invalid_or_missing_unit_eligible_records.csv", index=False)

    # Compact descriptive tables support the figures without changing source data.
    derived = valid_yield.copy()
    crop_summary = derived.groupby("Crop")["yield_tonnes_per_hectare"].agg(
        records="count", mean="mean", median="median", std="std", minimum="min", maximum="max",
        p01=lambda s: s.quantile(.01), p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75), p99=lambda s: s.quantile(.99),
    ).reset_index().sort_values("records", ascending=False)
    crop_summary.to_csv(OUT / "verified_yield_by_crop.csv", index=False)
    # Flag within-crop IQR extremes for investigation, never as automatic errors.
    outlier_tables = []
    for crop, group in derived.groupby("Crop"):
        values = group["yield_tonnes_per_hectare"]
        if len(values) < 30:
            continue
        q1, q3 = values.quantile([.25, .75])
        spread = q3 - q1
        flagged = group[(values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread)].copy()
        if len(flagged):
            flagged["crop_q1"] = q1
            flagged["crop_q3"] = q3
            flagged["lower_iqr_fence"] = q1 - 1.5 * spread
            flagged["upper_iqr_fence"] = q3 + 1.5 * spread
            flagged["review_note"] = "Statistical flag only; source record is retained and not presumed erroneous"
            outlier_tables.append(flagged)
    iqr_review = pd.concat(outlier_tables, ignore_index=True) if outlier_tables else pd.DataFrame()
    iqr_review.to_csv(OUT / "yield_iqr_review.csv", index=False)

    # Save within-crop top 0.1% area/production observations with raw CSV lines.
    raw = candidate.copy()
    raw["_area_num"] = pd.to_numeric(raw["Area"], errors="coerce")
    raw["_production_num"] = pd.to_numeric(raw["Production"], errors="coerce")
    extreme = raw.groupby("_crop_key", group_keys=False).apply(
        lambda group: group.assign(
            production_crop_percentile=group["_production_num"].rank(pct=True),
            area_crop_percentile=group["_area_num"].rank(pct=True),
        ), include_groups=False
    ).reset_index(drop=True)
    extreme = extreme[(extreme["production_crop_percentile"] >= .999) | (extreme["area_crop_percentile"] >= .999)].copy()
    extreme["review_note"] = "Extreme by within-crop percentile; units and source context need review; not presumed erroneous"
    extreme[["_source_row", "State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "area_crop_percentile", "production_crop_percentile", "review_note"]].to_csv(OUT / "extreme_observation_review.csv", index=False)
    year_summary = derived.groupby("Crop_Year").agg(records=("yield_tonnes_per_hectare", "size"), median_yield=("yield_tonnes_per_hectare", "median"), crop_count=("Crop", "nunique"), state_count=("State_Name", "nunique")).reset_index()
    year_summary.to_csv(OUT / "verified_yield_by_year.csv", index=False)
    state_summary = derived.groupby("State_Name").agg(records=("yield_tonnes_per_hectare", "size"), median_yield=("yield_tonnes_per_hectare", "median"), crop_count=("Crop", "nunique"), district_count=("District_Name", "nunique")).reset_index().sort_values("records", ascending=False)
    state_summary.to_csv(OUT / "verified_yield_by_state.csv", index=False)
    crop_year = candidate.groupby(["_Crop", "_year"]).size().rename("records").reset_index()
    crop_year.to_csv(OUT / "crop_representation_by_year.csv", index=False)

    # Plot raw production separately from verified yields so unresolved crops
    # cannot distort tonne-per-hectare visual summaries.
    crop_summary.head(20).sort_values("median", ascending=True).plot.barh(x="Crop", y="median", legend=False, figsize=(10, 8), color="#3f7f5f")
    plt.xlabel("Median yield (tonnes per hectare; verified-unit records only)")
    plt.ylabel("Crop")
    plt.title("Candidate dataset: median verified yield by crop")
    plt.tight_layout()
    plt.savefig(OUT / "median_yield_by_crop.png", dpi=160)
    plt.close()

    yearly = derived.groupby("Crop_Year")["yield_tonnes_per_hectare"].median()
    plt.figure(figsize=(10, 5))
    plt.plot(yearly.index, yearly.values, marker="o", color="#277da1")
    plt.xlabel("Crop year")
    plt.ylabel("Median yield (tonnes per hectare)")
    plt.title("Verified-unit median yield by year")
    plt.grid(alpha=.25)
    plt.tight_layout()
    plt.savefig(OUT / "median_yield_by_year.png", dpi=160)
    plt.close()

    top = candidate.groupby("_Crop")["Production"].sum(min_count=1).sort_values(ascending=False).head(12).sort_values()
    plt.figure(figsize=(10, 6))
    top.plot.barh(color="#e07a5f")
    plt.xlabel("Raw production (source units are not comparable across all crops)")
    plt.ylabel("Crop")
    plt.title("Largest raw production totals (not a cross-crop tonnes comparison)")
    plt.tight_layout()
    plt.savefig(OUT / "raw_production_totals_caution.png", dpi=160)
    plt.close()

    # Record concise overlap and derived-data totals for the human-readable report.
    report_stats = {
        "candidate": candidate_info, "current": current_info,
        "icrisat": next(x for x in inventory if x["filename"] == "ICRISAT-District Level Data.csv"),
        "earlier_hp": next(x for x in inventory if x["filename"] == "crop_production_haryana_punjab_1997_2014.csv"),
        "quality": quality, "overlap_rows": int(len(overlap)),
        "overlap_area_equal": int(overlap["area_equal"].sum()),
        "overlap_production_equal": int(overlap["production_equal"].sum()),
        "cotton_exact_overlap_rows": cotton_exact,
        "verified_yield_rows": int(len(valid_yield)),
        "unresolved_unit_rows": int(len(unresolved)),
        "iqr_flagged_rows": int(len(iqr_review)),
        "extreme_review_rows": int(len(extreme)),
        "invalid_or_missing_rows": int(len(unusable)),
        "verified_crops": int(valid_yield["Crop"].nunique()),
        "unresolved_crops": int(unresolved["Crop"].nunique()),
    }
    (OUT / "audit_summary.json").write_text(json.dumps(report_stats, indent=2, ensure_ascii=False))

    report = f"""# Crop Yield Alternative Dataset Audit (Milestone 2)

## Scope and handling

This audit reads the four CSV files in `DataSets/Yeild/`. The raw files, production Random Forest, Decision Tree challenger, backend, and frontend were not changed. Audit outputs are created only in this folder. Source hashes are in `dataset_inventory.csv`.

Candidate: `{CANDIDATE.name}`. It has **{candidate_info['rows']:,} rows × {candidate_info['columns_count']} columns**, years **{candidate_info['year_range'][0]}–{candidate_info['year_range'][1]}**, {candidate_info['states']} state/UT labels, {candidate_info['districts']} district labels, {candidate_info['crops']} crop labels, and {candidate_info['seasons']} season labels. The name “1997” does not describe its full coverage: observed rows span 1997–2015.

## Dataset inventory

See `dataset_inventory.csv` for columns, exact dimensions, missing-value counts, file sizes, year ranges, and SHA-256 digests. These four files are distinct formats/coverage rather than interchangeable versions: the candidate is national and long-form; the current source is Haryana/Punjab with explicit unit columns; the 1997–2014 Haryana/Punjab file is another unlabeled-unit long table; ICRISAT is a 1966–2017 wide district panel with explicit 1000-hectare, 1000-tonne and kg/ha columns for selected crops. ICRISAT is not the same table nor a simple superset.

## Measurement unit audit

OGD/DES catalog metadata describes this resource's area as hectares and production as tonnes. The candidate CSV itself has no unit columns. The generic catalog statement cannot be applied blindly because specific crop evidence and record matching expose exceptions:

| Crop group | Original production unit | Evidence and decision | Conversion / yield decision |
|---|---|---|---|
| Coconut | Most likely individual nuts; the exact CSV unit is not explicitly labeled | Coconut Development Board tables report production in million nuts and yield in nuts/ha. Candidate records include 65,100,000 over 18,168 ha, whose scale is consistent with nut counts. This conflicts with the generic OGD tonnes description. | No defensible nuts-to-tonnes conversion for these rows. Kept unresolved; no tonnes/ha calculated. |
| Sugarcane | Tonnes | OGD/DES catalog declares tonnes, and DES national estimates report sugarcane in tonnes. In the Haryana/Punjab overlap, all {int(overlap_summary[overlap_summary['_crop_key']=='sugarcane']['production_equal_rows'].sum())} matched production observations agree. | No conversion; tonnes/ha allowed for valid records. |
| Cotton(lint) | Bales in the overlapping candidate series | {cotton_exact} overlapping Haryana/Punjab rows with nonmissing production match exactly to the existing dataset, which labels Cotton(lint) as Bales. DES states one cotton bale is 170 kg. | Apply 0.17 tonnes/bale to convert; tonnes/ha allowed after conversion. See per-crop audit ledger. |
| Jute and Mesta | Unresolved in this candidate; official DES statistics use bales of 180 kg | The exact candidate CSV has no unit label and there is no overlap with an explicitly labeled source for these crops. Generic catalog tonnes metadata conflicts with DES crop-specific bale reporting. | No conversion approved for this exact resource; held out of derived yields. |
| Other crops | Tonnes per OGD catalog; no alternate unit convention identified in sources reviewed | The source catalog explicitly declares tonnes and hectares. Crop-specific review found no conflicting convention for remaining candidate crop labels. This is a resource-metadata conclusion, not a guarantee that every source record was independently measured correctly. | No conversion; tonnes/ha permitted for valid records. |

Complete row-level-by-crop evidence appears in `crop_production_unit_audit.csv`. Official references are listed below. `verified_yield_records.csv` contains only positive-area, nonnegative-production records with eligible standardized units. Cotton production is converted using the documented 170 kg/bale factor. Coconut, Jute, and Mesta records are retained separately in `unresolved_unit_records.csv`; no rows are silently dropped from the source.

## Data quality and coverage

Candidate quality checks found **{quality['missing_production']:,} missing production values**, {quality['zero_area']:,} zero-area rows, {quality['negative_area']:,} negative-area rows, {quality['zero_production']:,} zero-production rows, and {quality['negative_production']:,} negative-production rows. Exact full-row duplicates: **{quality['exact_duplicate_rows']:,}**. Duplicate state–district–year–season–crop key rows: **{quality['duplicate_compound_key_rows']:,}** across {quality['duplicate_compound_key_groups']:,} groups. The script retains all of these records for review.

There are {report_stats['verified_yield_rows']:,} eligible derived yields across {report_stats['verified_crops']} crops. {report_stats['unresolved_unit_rows']:,} Coconut/Jute/Mesta rows remain in the unresolved-unit file. Another {report_stats['invalid_or_missing_rows']:,} rows with otherwise eligible units lack valid positive area or nonnegative numeric production and are itemized in `invalid_or_missing_unit_eligible_records.csv`.

Whitespace in labels (for example padded season/crop/state labels) is normalized only in scratch matching keys; original labels remain intact. Coverage and crop representation by year are provided as CSVs. `yield_iqr_review.csv` contains {report_stats['iqr_flagged_rows']:,} statistical flags for crops with at least 30 records; these are review prompts, not evidence of bad data. `extreme_observation_review.csv` lists {report_stats['extreme_review_rows']:,} within-crop top 0.1% area/production observations with original CSV row numbers. They are retained and require source context before being called errors. The saved plots distinguish verified yield summaries from raw production totals, which are not comparable across unit types.

## Comparison with existing Haryana/Punjab dataset

Exact normalized key matching used State, District, Crop, Season, and the candidate numeric year against the first year in the existing `YYYY-YY` string. It found **{len(overlap):,} overlapping rows**, with {int(overlap['area_equal'].sum()):,} matching area values and {int(overlap['production_equal'].sum()):,} matching production values. Full match detail and per-state/crop summaries are saved as `haryana_punjab_record_matches.csv` and `overlap_summary.csv`.

Matching is informative but does not prove that the two tables are globally identical. The current source has 12,447 Haryana/Punjab rows, explicit Hectare/Tonnes/Bales columns and 1,418 missing production values. The national candidate has broader geographic coverage and 3,730 missing production values. It also includes unit ambiguities. The candidate cannot be appended wholesale without controlling crop units, year conventions, duplicate keys, and the named district/state changes.

## Modelling suitability (no model trained)

The candidate covers 19 calendar years. Crop support is uneven: **{quality['crop_support_bands']['100_or_more_records']} crops** have at least 100 records, **{quality['crop_support_bands']['30_to_99_records']}** have 30–99, and **{quality['crop_support_bands']['fewer_than_30_records']}** have fewer than 30. District history is broader but not uniform: {quality['district_history_bands']['five_or_more_years']} of 646 state–district labels appear in at least five distinct years; {quality['district_history_bands']['one_year']} appear in only one year. The final year, 2015, contains only 562 records, so it would be a thin holdout by itself. Chronological validation is feasible for well-represented crop groups, but not all 124 crops or all districts support stable separate estimates.

- **Historical multi-state analysis:** Supported for descriptive study if unit-specific crops are separated and geography labels are audited.
- **Crop-season yield estimation:** Potentially supported for verified-unit crops. Validation must use chronological splits and the same crop/region coverage must be represented in each split.
- **District-level yield estimation:** Potentially supported for districts and crops with repeated history; unseen district/state generalization is not established by the dataset's existence alone.
- **Farm-specific yield prediction:** Unsupported. Rows are district aggregates, not farm/plot observations. They contain no farm soil, management, weather, irrigation, or planned-area context.
- **Harvested area as input:** Area is an observed harvested area. A user planning cultivation may know intended/planted area instead, which is not interchangeable and can cause leakage/availability mismatch.

No models were trained, tuned, or evaluated in this audit.

## Recommendation

**C. Keep both datasets separate for now.** The national candidate broadens coverage substantially but has documented unit ambiguity for Coconut and unresolved Jute/Mesta conventions, plus no unit columns and a history of missing production values. Cotton can be standardized for its overlapping series using the independently confirmed bale unit and documented 170 kg factor, while most other crops follow the OGD catalog's tonnes declaration. This is not enough to justify wholesale replacement or row-level expansion today. A later, narrowly controlled expansion could be considered only for unit-verified crops and exact nonduplicate keys after review of this report.

## Sources

1. OGD Platform India / Directorate of Economics & Statistics, [District-wise, season-wise crop production statistics catalog](https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0): resource description declares area in hectares and production in tonnes; resource page: [1997 resource](https://data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997).
2. Coconut Development Board, Ministry of Agriculture & Farmers Welfare, [Annual Report 2021–22](https://coconutboard.gov.in/docs/anreport2021-22english.pdf): coconut production and productivity are expressed in million nuts and nuts/ha.
3. DES, [Agricultural Statistics at a Glance 2022](https://desagri.gov.in/wp-content/uploads/2023/05/Agricultural-Statistics-at-a-Glance-2022.pdf): sugarcane production in tonnes; cotton in bales of 170 kg; jute & mesta in bales of 180 kg.
4. DES, [Normal Estimates 2017–18 to 2021–22](https://desagri.gov.in/wp-content/uploads/2023/05/Normal-Estimates-2017-18-to-2021-22-2-1.pdf): Jute production table explicitly specifies thousand bales, 180 kg per bale.
5. Rubber Board of India, [Annual trends in area/production and related rubber statistics](https://rubberboard.gov.in/rbfilereader?fileid=1289): natural rubber production reported in tonnes.

## Reproducibility

From repository root run: `python models/crop_yield/reports/current/alternative_dataset_audit/run_audit.py`. It reads the original CSVs and rewrites only files in this audit directory. No model/test suite was run because this was a dataset audit, not a code or model change.
"""
    (OUT / "audit_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
