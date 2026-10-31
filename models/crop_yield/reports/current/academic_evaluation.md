# Crop yield model evaluation — Milestone 1

## Objective and dataset

Estimate the reported crop yield in tonnes per hectare for a crop and season. The primary source is `DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv`: 12,447 records, 10 columns, 1997-98 through 2019-20, and Haryana/Punjab district-level coverage. The target is the explicit `Yield` field. For compatible tonne/ha records, the source yield exactly matches production divided by area; Production is never a model input.

Preprocessing retained 9,882 records and excluded 2,565. Exact duplicates removed: 0. Exclusions were non-positive yield (2,057 rows) and incompatible non-tonne production units (626 rows), with 118 overlapping both reasons. Raw missing cells were 1,418, all in Production; accepted target records are present.

The dataset audit inspects 38 local yield/soil CSVs. The 1997-named all-India file actually spans 1997-2015, but its production and area units are undocumented. ICRISAT is a separate wide 80-column panel whose -1 semantics need source confirmation. Six SoilGrids layers have coordinate keys but no time; soil-nutrient samples are 2023-24/2024-25 and do not represent historic district averages. An existing NASA POWER service returns climatological/annual summaries or district fallbacks, not year/season-aligned historical weather. None are merged without defensible alignment. Provenance links are not present locally.

## EDA, cleaning and features

Yield varies strongly by crop: cleaned Wheat mean 4.38, Rice 3.31, and Sugarcane 64.35 t/ha. The 34 crops have imbalanced counts; the primary file contains 2 states, 45 districts and 3 seasons. Year distributions shift over time. IQR review flags 1,633 accepted rows, including an Onion/Karnal observation of 2 ha and 4,300 tonnes (2,150 t/ha). It is arithmetically consistent but plausibility is unresolved, so it remains flagged for review and retained.

The starting fields were State, District, Crop, Season, YearStart and Area. Validation-only feature ablation with Ridge alpha 10 found Crop+Season alone had MAE 2.8993, better than all six (3.3284). Adding state/district/year/area did not improve validation performance in this split. Grouped permutation on the selected validation pipeline increased MAE by 8.1913 t/ha when Crop was shuffled and 1.4197 when Season was shuffled. These are predictive associations, not causal effects. The final challenger therefore accepts only Crop and Season.

Production is excluded to prevent target leakage. Area is in hectares in the source; state/district/crop/season labels are trimmed and capitalization is handled in inference. Raw inputs remain unchanged. The selected challenger has a one-hot encoder fit on its training rows.

## Split and selection

| Partition | Years | Rows |
|---|---|---:|
| Training | 1997-2011 | 5,769 |
| Validation | 2012-2014 | 1,401 |
| Final test | 2015-2019 | 2,712 |

The validation period selects features and model by MAE, with RMSE as tie-breaker. For final test reporting, each candidate is refit on all records through 2014. Test metrics are reported after selection and are not used to choose a candidate.

MAE is mean absolute error; RMSE penalizes large errors more; R² describes explained target variation and can be negative when performance is worse than a constant mean predictor.

| Candidate (Crop and Season inputs) | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|---:|---:|---:|
| Decision Tree (depth None, min leaf 3) | 2.5300 | 6.4385 | 0.8806 | 2.4032 | 6.2134 | 0.8978 |
| Linear Regression | 2.5457 | 6.4448 | 0.8803 | 2.5761 | 6.2860 | 0.8954 |
| Lasso (alpha .001) | 2.5695 | 6.4583 | 0.8798 | 2.5967 | 6.3023 | 0.8948 |
| Random Forest | 2.6287 | 6.5272 | 0.8772 | 2.4552 | 6.2785 | 0.8956 |
| Ridge (alpha 10) | 2.8993 | 6.7740 | 0.8678 | 2.7455 | 6.4961 | 0.8883 |

A validation-only tree search used max_depth [None, 5, 10] and min_samples_leaf [3, 5, 10, 20]. The default candidate (None, 3) remained best; tuning did not improve it.

**Decision Tree with Crop and Season is the validation-selected challenger, not yet production.** The existing API artifact remains the six-feature Random Forest. The new challenger is in `artifacts/challenger_decision_tree_crop_season.joblib`, so no deployed artifact was silently replaced.

The selected tree's final test metrics are MAE 2.4032, RMSE 6.2134 and R² 0.8978. The production Random Forest separately measured 2.0995 / 9.2745 / 0.7723 on the same final years: the forest has lower average absolute error, but larger severe errors. The small crop-season tree has lower RMSE and higher R² in this test. The difference is not proof of future superiority. Feature selection, test-period distribution changes and source anomalies all limit confidence.

## Error analysis

The selected tree's error-analysis run reports: median residual (actual minus prediction) 0.2196 t/ha and 95th-percentile absolute error 16.1645 t/ha. Large errors concentrate in high-yield Sugarcane records. The module retains per-row test predictions, crop/state/year error tables and a residual plot. No difficult record was dropped to improve scores.

## Reproduction and verification

Run from the repository root, in this order:

1. `.venv/bin/python models/crop_yield/eda/audit_datasets.py`
2. `.venv/bin/python models/crop_yield/preprocessing/prepare_data.py`
3. `MPLCONFIGDIR=/private/tmp/agrioptima-mpl .venv/bin/python models/crop_yield/eda/run_eda.py`
4. `.venv/bin/python models/crop_yield/training/feature_ablation.py`
5. `.venv/bin/python models/crop_yield/training/tune_model.py`
6. `.venv/bin/python models/crop_yield/training/train_compare_models.py`
7. `MPLCONFIGDIR=/private/tmp/agrioptima-mpl .venv/bin/python models/crop_yield/evaluation/error_analysis.py`
8. `.venv/bin/python models/crop_yield/training/train_challenger.py`
9. `.venv/bin/python models/crop_yield/evaluation/evaluate.py` (reports current production Random Forest)
10. `.venv/bin/python -m pytest -q models/crop_yield/tests backend/tests`

Executed workflow verification: **29 tests passed**, with one existing Starlette/httpx deprecation warning. Yield inference tests check both saved artifacts, supported input fields, missing fields, invalid year/area, and unknown labels. The candidate inference schema is Crop and Season; production Random Forest schema remains State, District, Crop, Season, YearStart and Area.

## Review gate and limits

The candidate covers only Haryana and Punjab history and cannot account for field-specific weather, soil, irrigation or management. Crop-season-only predictions also omit geography and year because they did not improve this validation metric. The 2012-2014 and 2015-2019 yield distributions differ; model ranking depends on the selected window and metric.

Review the source exclusions, the unusual retained records, and whether to promote the Decision Tree challenger. No other ML module or frontend was changed; work stops here pending review.
