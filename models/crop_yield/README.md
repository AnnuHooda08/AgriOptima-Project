# Crop yield prediction

## Scope and problem

This module predicts **reported crop yield in tonnes per hectare** for a crop/state/district/season/year/area combination represented in the Haryana and Punjab training records. Yield is output per unit of cultivated area; total production is a different quantity. A prediction is a historical-data-based estimate, not a promise of a farmer's harvest.

The primary file has an explicit `Yield` column. Its values match `Production / Area` for records with compatible numeric units (the source production unit includes both tonnes and bales). The model uses the explicit `Yield` target and never uses `Production` as an input. Bales records are excluded because their production unit cannot safely be treated as tonnes. Area is in hectares.

## Source audit and selection

Run `python models/crop_yield/eda/audit_datasets.py` to regenerate the inventory CSV, full schemas, and audit summary in `reports/current/`. The checked-in audit covers 38 crop/soil CSV files. Exact local provenance links are not recorded in repository metadata; the audit therefore reports filenames and structures rather than guessing external sources.

| Dataset | Records / columns | Coverage and fields | Decision |
|---|---:|---|---|
| `DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv` | 12,447 / 10 | Crop years 1997-98 to 2019-20; Haryana and Punjab; State, District, Crop, Year, Season, Area, units, Production, Yield | **Primary.** Long district-level records, explicit yield and units, and the longest directly compatible Haryana/Punjab panel. |
| `DataSets/Yeild/crop_production_haryana_punjab_1997_2014.csv` | 9,048 / 7 | 1997-2014; Haryana and Punjab; area/production but no explicit units or yield | Excluded from fitting because it overlaps the primary source and adds unit/target ambiguity. |
| `DataSets/Yeild/district_wise_season_wise_crop_production_1997.csv` | 246,091 / 7 | India, 1997-2015 (filename is misleading); state/district/crop/season/area/production | Excluded: it has a longer national panel, but no explicit units or yield column, and local provenance is undocumented. Target derivation/combination would require unsupported unit assumptions. |
| `DataSets/Yeild/ICRISAT-District Level Data.csv` | 16,146 / 80 | India, 1966-2017; 20 states and 311 districts; wide crop-specific area/production/yield fields | Reference / possible external validation only. It is wide, has `-1` values requiring source-semantic confirmation, and needs careful crop mapping and unit harmonization before it can be joined. |
| Six `DataSets/Soil Grid/soilgrids_*.csv` files | 249,001 / 13 each | Coordinate grid; depth-specific pH, organic carbon, nitrogen, texture, density, CEC and coarse fragments; no dates | Not joined. They have no district key or time dimension, so attaching values to historic production rows would require a defensible spatial lookup and would still be static over years. |
| 28 `DataSets/Soil nutrient/soil-nutrient-analysis.part-*.csv` shards | 10,853,209 total / 14 | Recent survey observations (2023-24 and 2024-25); state/district/block/village and nutrient/value | Not joined. This survey does not align in time with 1997-2019 harvest rows; field-level sampling is not the same as a representative historical district value. |
| Weather / rainfall / temperature | No historical weather file found under `DataSets/`; existing service is `backend/app/services/weather_service.py` | NASA POWER climatology endpoint with district-baseline fallbacks; annual/climatological values, not historic year/season records | Not integrated: there is no year- and season-aligned weather history to match the 1997-2019 harvest rows. The service is noted as a future source once compatible historical data is obtained. |

Missing-cell percentages, schemas and the full filename-level records are in `reports/current/yield_dataset_inventory.csv` and `reports/current/yield_dataset_schemas.json`. The primary source has 1.14% missing cells overall, mostly missing production; its target itself is present in the accepted rows. All source files remain in place and are read-only to the pipeline.

## Target and leakage controls

- Target: `Yield`, in tonnes per hectare.
- Model inputs: `State`, `District`, `Crop`, `Season`, `YearStart`, and `Area` (hectares).
- `YearStart` is the first four-digit year parsed from the crop-year label, such as `1997-98`.
- `Production` is deliberately absent from the feature list because it is used to calculate/verify yield in the source. Including it would reveal the answer.
- The fitted one-hot encoder is inside each scikit-learn pipeline. It is fit only on each training partition.

## Cleaning and preprocessing

`preprocessing/prepare_data.py` leaves raw CSVs unchanged and writes a clean copy, model-ready features, and an excluded-row audit. It trims text, parses numeric values and years, removes exact duplicate rows, rejects blank required categories, invalid/non-positive area or yield, and incompatible area/production units. It does not clip valid-looking high yields simply because they are unusual.

Current run: **12,447 source rows; 0 exact duplicates; 9,882 accepted; 2,565 excluded**. Exclusions are non-positive yields and rows whose production unit is not tonnes (these groups overlap). Area units are hectares. IQR flags are saved for review only; they are not automatic deletions.

## EDA findings

Run `eda/run_eda.py`. Nine labelled plots are saved under `eda/plots/`, while numeric profiles and summaries are saved in `reports/current/`.

- The accepted data covers 2 states, 45 districts, 34 crops and 3 seasons. Records are imbalanced by crop: Wheat has 915 rows, Rice 890, and uncommon crops have much less.
- Yield varies strongly by crop. In the cleaned data Wheat's mean is about 4.38 t/ha, Rice about 3.31, while Sugarcane is about 64.35. This explains why pooled error can hide crop-specific mistakes.
- State-wide mean yields are close (Haryana 6.64, Punjab 6.75 t/ha), but these averages combine very different crops. Whole Year crops have a much higher median (about 17.17) than Kharif (1.00) or Rabi (1.44).
- Year-wise yield distribution changes materially; the median rises from about 1.64 t/ha in the training years to 2.44 in validation and 2.48 in the test years. The upper tail also rises, so a chronological test is necessary.
- Numerical correlations are weak between yield and area (-0.034 in raw EDA; -0.056 in clean model rows) and between yield and year (about 0.05 raw). Crop and season carry much more signal in the held-out validation data than the numeric features or district/state labels.
- An IQR rule flags 1,633 accepted rows for human review. One conspicuous record is Onion in Karnal, 2008-09: area 2 ha, production 4,300 tonnes, yield 2,150 t/ha. It is mathematically consistent with the source's production/area fields, but its agricultural plausibility needs source-owner review. It was retained rather than silently discarded. Large sugarcane yields also drive many of the largest model residuals.

## Feature decisions

The initial feature set was State, District, Crop, Season, YearStart and Area. A validation-only ablation with Ridge (alpha 10) found that Crop and Season alone performed best: MAE 2.8993 t/ha versus 3.3284 with all six fields. Removing Area or YearStart individually changed full-feature MAE only slightly; state/district and the numeric fields did not add measurable validation value in this split. On that evidence, the selected challenger uses only Crop and Season. Grouped permutation importance on the validation window also ranked Crop first (MAE increased by 8.1913 when shuffled) and Season next (increase 1.4197). These are validation associations, not causal effects.

One-hot encoding is wrapped in the saved pipeline and fit on training data only. The selected model has no numeric features, so it does not need an imputer or scaler. The current production Random Forest remains a six-feature pipeline until you approve a replacement.

Soil nutrients, SoilGrids and historical weather are not included because no reliable time-and-geography join is established. Production is excluded for leakage. No standalone row ID or derived target component is used.

## Validation and candidate models

The split follows time order:

| Partition | Years | Rows |
|---|---|---:|
| Training | 1997-2011 | 5,769 |
| Validation | 2012-2014 | 1,401 |
| Final test | 2015-2019 | 2,712 |

Validation selects the candidate by MAE (RMSE breaks ties). Then each candidate is refit on all pre-2015 records and measured once on 2015-2019. The final test metrics are descriptive and were not used to choose the winner.

Feature selection is performed using the training and validation periods only. The grouped validation ablation results are in `evaluation/feature_ablation_validation.csv`; `evaluation/feature_importance_validation.csv` records the selected two fields' permutation importance.

Metrics below were generated by `training/train_compare_models.py` after selecting Crop and Season. MAE/RMSE are tonnes/hectare (lower is better); R² measures explained variation (closer to 1 is better and can be negative).

| Model | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|---:|---:|---:|
| Decision Tree (min leaf 3) | 2.5300 | 6.4385 | 0.8806 | 2.4032 | 6.2134 | 0.8978 |
| Linear Regression | 2.5457 | 6.4448 | 0.8803 | 2.5761 | 6.2860 | 0.8954 |
| Lasso (alpha .001) | 2.5695 | 6.4583 | 0.8798 | 2.5967 | 6.3023 | 0.8948 |
| Random Forest | 2.6287 | 6.5272 | 0.8772 | 2.4552 | 6.2785 | 0.8956 |
| Ridge (alpha 10) | 2.8993 | 6.7740 | 0.8678 | 2.7455 | 6.4961 | 0.8883 |

### Selection and tuning decision

**Decision Tree using Crop and Season is the validation-selected challenger, not yet the production model.** It has the lowest validation MAE and slightly lower validation RMSE than the other models. It gives a crop-season typical-yield estimate and cannot distinguish districts, years or field area; that is a real limitation, despite this small dataset showing no validation benefit from those fields.

A small tree search tested max_depth `None/5/10` and min_samples_leaf `3/5/10/20`. The best validation setting was the existing simple choice (`max_depth=None`, `min_samples_leaf=3`), so tuning did not improve it. Test scores were generated only after validation/model/feature selection and were not used to pick the candidate.

The selected tree's final test metrics are MAE 2.4032, RMSE 6.2134 and R² 0.8978. The existing six-feature Random Forest has MAE 2.0995, RMSE 9.2745 and R² 0.7723 on the same final years: its average absolute error is lower, but it has much larger severe errors. The crop-season tree provides more balanced RMSE/R² in this holdout. Because the same final years were used to report several candidate comparisons and the split distribution changes over time, this is not proof of future superiority. The challenger is saved separately as `artifacts/challenger_decision_tree_crop_season.joblib`; the existing API artifact `artifacts/random_forest.joblib` remains unchanged pending your review.

## Error analysis

`evaluation/error_analysis.py` evaluated the validation-selected Decision Tree on the final 2015-2019 holdout:

- MAE 2.4032 t/ha, RMSE 6.2134 t/ha, R² 0.8978.
- Median residual (actual minus prediction) 0.2196 t/ha; the median bias is small.
- 95th percentile absolute error: 16.1645 t/ha.
- The largest errors are primarily high-yield Sugarcane records. These are retained and reported, not hidden.

Per-crop, per-state, per-year error tables, all test predictions, a residual plot, and the largest errors are in `evaluation/`.

## Reproducible commands

Run these from the repository root. Use the repository virtual environment so saved scikit-learn artifacts use the project's installed version.

```bash
.venv/bin/python models/crop_yield/eda/audit_datasets.py
.venv/bin/python models/crop_yield/preprocessing/prepare_data.py
MPLCONFIGDIR=/private/tmp/agrioptima-mpl .venv/bin/python models/crop_yield/eda/run_eda.py
.venv/bin/python models/crop_yield/training/feature_ablation.py
.venv/bin/python models/crop_yield/training/tune_model.py
.venv/bin/python models/crop_yield/training/train_compare_models.py
MPLCONFIGDIR=/private/tmp/agrioptima-mpl .venv/bin/python models/crop_yield/evaluation/error_analysis.py
.venv/bin/python models/crop_yield/training/train_challenger.py
.venv/bin/python -m pytest -q models/crop_yield/tests
```

The existing production Random Forest evaluation/artifact can be reproduced separately with:

```bash
.venv/bin/python models/crop_yield/evaluation/evaluate.py
.venv/bin/python models/crop_yield/training/train.py
```

The second command overwrites the current Random Forest artifact, so run it only when you intend to refresh that same model. Candidate inference can use the challenger explicitly:

```python
from models.crop_yield.inference.predict import predict
prediction = predict({
    "Crop": "Wheat", "Season": "Rabi"
}, "models/crop_yield/artifacts/challenger_decision_tree_crop_season.joblib")
```

The selected challenger needs only a known Crop and Season from this dataset; capitalization is normalized. The production Random Forest still needs all six documented inputs, including an integer YearStart and positive Area in hectares. The returned float is tonnes per hectare. Unknown categories and invalid inputs raise a readable error.

## Module contents

- `eda/`: dataset inventory and reproducible descriptive analysis / plots.
- `preprocessing/`: raw-data validation and clean modeling table.
- `training/`: feature ablation, model comparison, small decision-tree tuning search, challenger training, and existing production-model training.
- `evaluation/`: holdout metrics, comparison table, residual analysis, and test predictions.
- `artifacts/`: existing production Random Forest and separate Decision Tree challenger.
- `tests/`: data contract, artifact, prediction and invalid-input checks.
- `reports/current/`: generated audit, preprocessing, and EDA outputs.
- `reports/legacy/`: prior diagnostic outputs preserved for academic history.

## Limitations and review gate

The records cover only Haryana and Punjab and use historic reported production, which may include data-entry/unit errors. Features do not include weather or soil measurements, and the model cannot predict crop failures caused by unobserved conditions. Category support is limited to known training labels. Test performance changes across time windows and crop groups; do not interpret aggregate R² as a farmer-level guarantee.

**Review gate:** the yield workflow is complete for review. No other model or frontend was changed. Please review the dataset exclusions and whether to promote the Decision Tree challenger before any production artifact replacement or moving to another module.
