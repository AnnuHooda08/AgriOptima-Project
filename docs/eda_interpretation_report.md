# AgriOptima EDA Interpretation Report

**Evidence basis.** This report uses the generated files under `reports/`, the generated plots under `plots/`, the CSV schemas and samples under `DataSets/`, and additional read-only checks run against the manageable CSVs and the 28 split parts of the soil-nutrient dataset. The EDA pipeline analyzed the complete smaller datasets and sampled 50,000 rows for the large production, SoilGrids, and soil-nutrient files. Therefore, sampled report statistics are labelled as sampled; row counts and the chunked soil-nutrient checks are full-file facts.

No raw dataset was modified. No ML model was trained.

## 1. Dataset Inventory

| Logical dataset | Size | Rows | Columns | Time coverage | Geography | Important variables | Type | AgriOptima role |
|---|---:|---:|---:|---|---|---|---|---|
| `crop_production_haryana_punjab_1997_2014.csv` | 0.46 MB | 9,048 | 7 | 1997-2014 | Haryana, Punjab; district level | Crop, season, area, production | Production panel without yield | Candidate yield/production source; production has 1,365 missing values |
| `crop_production_haryana_punjab_1997_2019.csv` | 0.97 MB | 12,447 | 10 | 1997-98 to 2019-20 | Haryana, Punjab; district level | Crop, season, area, production, yield, units | Production/yield panel | Candidate yield source; production has 1,418 missing values |
| `india_crop_production_kaggle_mirror_1997_2014.csv` | 14.61 MB | 246,091 | 7 | `Crop_Year` 1997-2015 in the file | 33 states/territories; district level | Crop, season, area, production | National production panel without yield | Candidate national production source; production has 3,730 missing values |
| `india_district_crop_production_1997_2019.csv` | 29.56 MB | 345,407 | 10 | 1997-98 to 2020-21 in the file | 36 states/territories; district level | Crop, season, area, production, yield, units | National production/yield panel | Primary candidate for national yield modelling; production has 4,993 missing values |
| `ICRISAT-District Level Data.csv` | 8.83 MB | 16,146 | 80 | 1966-2017; 52 years | 20 states, 311 districts | Wide crop-specific area, production, yield columns | Wide production/yield panel | Historical supporting/reference dataset; requires sentinel and wide-to-long treatment |
| `post_harvest_loss_2022_haryana_punjab.csv` | 0.01 MB | 164 | 9 | 2022 only | Haryana, Punjab | Crop, loss type, stage, loss percentage | Source-extracted loss table | Candidate regional loss analysis; small and source-table-specific |
| `post_harvest_loss_2022_state_stage.csv` | 0.12 MB | 1,865 | 9 | 2022 only | 19 states | Crop, loss type, stage, loss percentage | Source-extracted loss table | Candidate broader loss model; source-table-specific |
| `fao_food_loss_export_2026-09-17.csv` | 7.02 MB | 30,361 | 18 | 2000-2024 | International; country/region | Commodity, stage, loss percentage, method, quantity | FAO food-loss observations/estimates | Reference or candidate loss dataset; metadata is sparse and methods vary |
| `soil-nutrient-analysis.csv` represented by `soil-nutrient-analysis.part-001.csv` through `part-028.csv` | 1,046.02 MB original; split for GitHub | 10,853,209 | 14 | 2023-24 and 2024-25 | 32 states; district/block/village fields | Nutrient name, nutrient level, value, location codes | Stacked soil survey records | Supporting soil/nutrient classification and feature source |
| Six SoilGrids layers | 16.07-16.93 MB each | 249,001 each | 13 each | No date column | Coordinate grid spanning latitude 27.508364-32.698805 and longitude 73.701130-77.996609 | pH, organic carbon, nitrogen, texture, density, CEC, coarse fragments | Gridded soil profiles | Candidate geospatial soil features |

### Overlap and retention

The two Haryana/Punjab files share geography and much of the crop-production subject matter, but they differ in schema, time coverage, crop counts, and availability of `Yield`. The 1997-2014 file has 43 crops and no yield column; the 1997-2019 file has 39 crops and a yield column. They are not proven row-for-row duplicates: the direct duplicate check found zero duplicate rows within each file, but a cross-file key comparison has not yet been performed. Retain both until a normalized key comparison (`state`, `district`, `crop`, `season`, `year`) determines whether one is an extension, revision, or alternate extract.

The two national production files also overlap conceptually but differ in coverage and schema. The Kaggle mirror has 246,091 rows, 33 states, 124 crops in the generated categorical summary, and no yield column. The 1997-2019 district file has 345,407 rows, 36 states, 56 crops, and yield. Their names, years, crop vocabularies, units, and missingness differ, so automatic deletion is not justified. Retain both as candidate/reference sources until reconciliation.

ICRISAT overlaps with the crop-production panels in area, production, and yield, but it is a separate wide historical source with 1966-2017 coverage and 20 states. It should be retained for historical context and validation, not blindly appended to the long-format panels.

## 2. Data Quality Findings

### Missing values

| Dataset | Finding | Why it matters | Treatment |
|---|---|---|---|
| Haryana/Punjab 1997-2014 | `Production`: 1,365/9,048 (15.09%) missing | Production cannot be used directly as a target or denominator for those rows | Investigate whether missing means unavailable or zero; do not impute before checking source semantics |
| Haryana/Punjab 1997-2019 | `Production`: 1,418/12,447 (11.39%) missing | A yield/production relationship is incomplete | Preserve missingness; derive or validate yield only where inputs are valid |
| National Kaggle mirror | `Production`: 3,730/246,091 (1.52%) missing | Affects production modelling and reconciliation | Investigate by crop/year/state; avoid blanket imputation |
| National 1997-2019 | `Production`: 4,993/345,407 (1.45%); `Area`, `Yield`, `Crop`, and `Season` each have a small number of missing rows | Some records cannot safely enter a supervised feature matrix | Exclude or separately repair rows after key-level investigation |
| FAO food loss | `notes` 96.72%, `cause_of_loss` 96.60%, `sample_size` 95.34%, `treatment` 95.09%, `region` 94.73%, `loss_quantity` 83.95%, `food_supply_stage` 11.17% missing | Loss estimates have uneven metadata and may not be comparable | Keep the loss percentage, but stratify/flag by method, stage, and metadata completeness |
| Soil-nutrient parts | No missing fields in the generated report or chunked checks | Completeness does not remove unit/semantic risk | Keep values, then validate units by nutrient |
| SoilGrids | No missing fields in any layer | Good structural completeness | Validate physical ranges and coordinate alignment before merging |
| Post-harvest 2022 tables | No missing fields | These tables are structurally complete | Retain source provenance columns and source-table boundaries |

### Duplicates and identifiers

The direct check found zero duplicate rows in each manageable production/loss CSV. The FAO food-loss file contains 180 duplicate rows; these require key-definition investigation before deduplication because repeated observations may represent separate sources or methods. The soil-nutrient dataset has 10,853,209 unique `id` values and zero repeated IDs, but only 287,331 unique location combinations and every location has multiple rows. This is expected for multiple nutrients and survey observations, not evidence of duplicate records by itself.

### Invalid, negative, zero, and special values

- The ICRISAT report shows negative values in many crop area, production, and yield columns. Because the minimum is exactly `-1` across these measures, `-1` is highly suspicious as a missing/not-available sentinel rather than a physical agricultural measurement. Recode `-1` to missing only after confirming the source documentation; never use it as a numeric value.
- ICRISAT also has many zeros. Some are plausible non-production or non-cultivation observations, especially for crop/district combinations, while others can be missing-code artifacts. Treat zero area as a structural absence candidate; do not globally convert every zero to missing.
- Production panels contain legitimate zero production counts and zero yields. For example, the Haryana/Punjab 1997-2019 file has 639 zero production values and 2,057 zero yields; the national 1997-2019 file has 151 zero production values and 830 zero yields. Investigate whether zero yield is consistent with zero area/production before treatment.
- The soil-nutrient file has 4,130,027 zero `value` observations out of 10,853,209. Since `value` combines 12 nutrient concepts with different scales, zero must be evaluated within `nutrient_name`; it cannot be globally removed.
- SoilGrids depth fields are constant by layer by design. `depth_top_cm=0` in the 0-5 cm layer is valid, not an error.

### Outliers and units

The IQR report flags many production and area values because agricultural production is naturally heavy-tailed across districts and crops. The Haryana/Punjab 1997-2019 report flags 19.19% of area and 20.15% of production as sampled IQR outliers; this is not sufficient evidence for deletion. Use robust transforms, log features where appropriate, crop/state stratification, and domain review.

Units are not consistent across all production tables: the Haryana/Punjab 1997-2019 table uses `Area Units=Hectare` and has `Production Units=Tonnes` or `Bales`; the national table has `Production Units=Tonnes`, `Bales`, and `Nuts`. Harmonize units before any cross-dataset merge. A yield target must also have a consistent unit; do not assume that the reported `Yield` is comparable across files until its derivation and units are verified.

## 3. Numerical Analysis

### Identifier and code columns

Treat `id`, `Dist Code`, `State Code`, `District Code`, `Block Code`, `Village Code`, `m49_code`, `cpc_code`, and source page/table/row fields as identifiers or metadata. Do not standard-scale them as continuous agricultural features or interpret their IQR outliers as agronomic anomalies. The high correlations among soil-nutrient administrative codes are code hierarchy effects, not agricultural relationships.

### Continuous measurements and targets

- **Production area:** Area is positive and extremely right-skewed in production panels. The national 1997-2019 area ranges from 0.004 to 8,580,100, and the Haryana/Punjab 1997-2019 area ranges from 1 to 422,000. Log transformation and crop/state stratification are candidates; validate units first.
- **Production:** Production includes missing and zero values and is highly right-skewed. It may be a target for a production model, but it is not a safe predictor of yield when yield is derived from production and area.
- **Yield:** The Haryana/Punjab yield summary has mean 6.677, standard deviation 24.724, range 0-2,150; the national summary has mean 79.408, standard deviation 916.627, range 0-43,958. These differences strongly suggest unit or scale differences and require validation before pooling. Yield is a candidate target, not automatically a comparable feature.
- **FAO loss percentage:** The 30,361-record file has loss percentage range 0-65 and mean 4.481; the original loss percentage field has missing values. The measurement method is heterogeneous, so transformations and model stratification should follow method/stage/source checks.
- **Post-harvest 2022 loss:** The Haryana/Punjab table ranges from 0.00004 to 6.67; the state-stage table ranges 0-13.19. These are not automatically comparable to FAO values or to one another because source tables and definitions differ.
- **SoilGrids:** Across layers, pH means rise from 7.499 at 0-5 cm to 7.736 at 100-200 cm; organic carbon falls from 21.361 to 5.482 g/kg; total nitrogen falls from 1.941 to 0.618 g/kg; bulk density rises from 1.398 to 1.477 g/cm3; coarse fragments rise from 10.077% to 14.163%. These are observed depth-stratified differences, not causal claims. The layer-specific IQR flags are often large for organic carbon, nitrogen, and density, so retain and inspect rather than delete.
- **Soil nutrient `value`:** The full range is 0-10,205, but this single column mixes Nitrogen, Organic Carbon, Phosphorus, Potassium, pH, Electrical Conductivity, Iron, Manganese, Zinc, Boron, Copper, and Sulphur. It is not a single comparable measurement. Split or model by nutrient name and verify units before scaling or interpreting distributions.

The SoilGrids report shows strong correlations, including organic carbon-total nitrogen 0.954 and sand-silt -0.904 in the 0-5 cm layer. These are useful for feature review but do not establish causality. They also imply possible multicollinearity; compare models with feature selection or regularization.

## 4. Categorical Analysis

- Production datasets are dominated by common crops such as Rice, Wheat, Maize, pulses, and sugarcane, but their crop vocabularies differ substantially: 43 vs 39 crops in the Haryana/Punjab files, 124 in the Kaggle mirror summary, and 56 in the national 1997-2019 file. Normalize spelling, punctuation, aliases, and crop taxonomy before comparison.
- Season categories are imbalanced but not single-class. Kharif is the largest category in the Haryana/Punjab files (48.82% in 1997-2014; 48.06% in 1997-2019); Rabi is next; Whole Year is smaller. The Kaggle mirror also contains Summer, Winter, and Autumn with padded whitespace in category values. Trim and normalize categories.
- The Haryana/Punjab production data are geographically imbalanced toward Haryana: 64.93% in 1997-2014 and 66.72% in 1997-2019. The national data are dominated by Uttar Pradesh, Madhya Pradesh, Karnataka, and Bihar. Use grouped or stratified evaluation so the model is not judged only on dominant regions.
- The soil-nutrient dataset contains 12 nutrient names, 2 nutrient types (`Macro`, `Micro`), and 10 level labels. Macro records are 6,362,190 and micro records 4,491,019. Nutrient-level labels are concept-specific: `High/Medium/Low` for some nutrients, `Deficient/Sufficient` for others, and `Acidic/Neutral/Alkaline` or `Saline/Non Saline` for pH/EC. Do not combine these labels into one ordinal scale.
- Post-harvest data contain 17 stages and multiple loss types. The state-stage table is not a crop-only classification dataset: it includes commodities such as milk, meat, fish, poultry, and crops. Define the modelling population before encoding.
- FAO `food_supply_stage` has 20 categories, but 3,391 records are missing and the distribution is dominated by Farm, Whole supply chain, and Harvest. Rare stages may need grouping only after confirming the modelling target and evaluation design.

## 5. Time-Series Analysis

Observed coverage differs by source:

- ICRISAT: 1966-2017, 52 years.
- Haryana/Punjab 1997-2014: 18 years.
- Haryana/Punjab 1997-2019: 23 agricultural-year labels from 1997-98 through 2019-20.
- National Kaggle mirror: `Crop_Year` 1997-2015 in the file.
- National 1997-2019: 1997-98 through 2020-21, with 24 distinct year labels.
- Soil nutrient: only 2023-24 and 2024-25, with 65.44% and 34.56% of records respectively.
- FAO food loss: 2000-2024.
- Post-harvest 2022 tables: 2022 only.
- SoilGrids: no time column.

The production tables have missing values and unequal row counts by year, so observed year-to-year changes cannot be interpreted as pure production trends without normalizing by crop, geography, area, and coverage. The national 1997-2019 table includes one 2020-21 label while its filename says 1997-2019; this is a schema/coverage naming issue to investigate. The soil-nutrient data are too short in time to support a long-term trend claim.

**Observed pattern:** source coverage, not causal trend, is established by the current EDA. **Possible explanation:** changes in reporting, crop/geography coverage, agricultural-year conventions, or actual production changes. Additional grouped time-series tables are required before claiming trends.

## 6. Agriculture-Specific Findings

- Crop production is recorded at different granularities: district-crop-season-year in long panels, crop columns in ICRISAT, nutrient/location/year in the soil survey, and coordinate-depth in SoilGrids.
- Area and production are strongly associated in the Haryana/Punjab 1997-2019 report (correlation 0.819), but the national report’s sampled correlation is only 0.049. This difference is a warning about aggregation, missingness, units, crop mix, and source construction; it is not a contradiction to be averaged away.
- Yield and production correlation is 0.173 in the Haryana/Punjab report and 0.443 in the national report. Because yield may be mathematically derived from production and area, these correlations are not evidence that production is a valid prediction feature.
- SoilGrids shows systematic depth changes in carbon, nitrogen, density, pH, and coarse fragments. A depth-aware soil representation is more appropriate than treating layers as interchangeable rows.
- Post-harvest loss stage counts are led by transport and aggregate farm/market-operation stages in the 2022 tables. Stage-level observations must remain separate from total-loss rows to avoid double counting.

## 7. Soil Nutrient Analysis

The logical soil-nutrient dataset has 10,853,209 rows, no missing fields, 32 states, 735 district names, 6,289 block names, 100,000 village names, two years, 12 nutrient names, and 10 nutrient-level labels. The full chunked check found values from 0 to 10,205, 4,130,027 zero values, 10,853,209 unique IDs, and no duplicate IDs. There are 287,331 unique state-district-block-village location combinations; every location repeats, with a maximum of 147 rows per location, which is expected from multiple nutrients, levels, and years.

Nutrients are: Nitrogen, Organic Carbon, Phosphorus, Soil Ph, Potassium, Electrical Conductivity, Iron, Manganese, Zinc, Boron, Sulphur, and Copper. Macro records are 58.61% and micro records 41.39% by the full chunked count. The balanced-looking nutrient-level combinations are concept-specific: for example, pH uses Acidic/Neutral/Alkaline, EC uses Saline/Non Saline, macro nutrients use High/Medium/Low, and trace nutrients use Deficient/Sufficient.

The source encoding is a major issue: the current CSV exposes `state_name`, `district_name`, `block_name`, and `village_name` as integer-coded fields in the generated schema, not readable names. The report’s heuristic also misidentified `block_name` as organic carbon. This means the meaning of those coded columns must be verified from the source data dictionary before joining to other geographic data.

The `value` column must never be interpreted globally. Units and valid ranges can differ by nutrient; the same number may mean different things for pH, concentration, or electrical conductivity. Keep `nutrient_name` and `nutrient_type` attached, validate units, and reshape to a nutrient-specific long or location-wide representation only after validation.

## 8. SoilGrids Analysis

All six SoilGrids files have the same 13-column schema, 249,001 rows, no missing values, and the same coordinate range. Their layer depths are constant and distinct: 0-5, 5-15, 15-30, 30-60, 60-100, and 100-200 cm. The evidence supports aligned coordinate grids; the current checks found no duplicate full rows within the individual layer files.

Do not merge them as ordinary row append operations without a depth field. The safe strategy is:

1. Read each layer with explicit `depth_top_cm` and `depth_bottom_cm`.
2. Validate that `(latitude, longitude)` keys align across all six layers.
3. Either concatenate to a long table with a `depth_interval` key, or pivot to one row per coordinate with names such as `ph_h2o_0_5`, `ph_h2o_5_15`, and so on.
4. Keep the long form as the canonical representation and derive a wide ML matrix only for a defined modelling task.
5. Do not join SoilGrids to district production until a documented spatial assignment from coordinates to district/state is created; there is no district key in SoilGrids.

The depth means show lower organic carbon and nitrogen, higher bulk density and coarse fragments, and slightly higher pH at depth. These are supported descriptive patterns.

## 9. Crop Production & Yield Analysis

The long production panels are the most natural starting point for yield modelling because they expose crop, geography, season, year, area, production, and sometimes yield as rows. The national 1997-2019 file is the strongest candidate among the current files for a national yield target, but it still has 4,993 missing production values, 33 missing area/yield values, and a production-unit mixture that requires cleaning.

### Target leakage

If `Yield = Production / Area` or an equivalent directly derived quantity, including `Production` as a predictor leaks information from the target into the feature set. For yield prediction, exclude production and any post-outcome aggregate derived from it. Candidate pre-outcome features include crop, state/district, season, year, area where scientifically appropriate, soil variables, and weather variables after alignment. If the target definition is not confirmed, calculate the identity on valid rows and compare units before finalizing the feature contract.

### ICRISAT

ICRISAT has 80 columns: administrative keys, year, and repeated Area/Production/Yield groups for crops. It is wide and has 16,146 rows, 311 district codes, 20 state codes, and 52 years. Its values include `-1` minima and many zeros. Keep the raw wide file as reference, but transform a copy to long form for ML:

```text
Dist Code | State Code | State Name | Dist Name | Year | Crop |
Area_1000_ha | Production_1000_tons | Yield_kg_per_ha
```

The transformation must map each crop’s three columns explicitly and preserve the original units. Do not transform the raw file in place.

## 10. ICRISAT Analysis

The automated dataset-family detector labelled ICRISAT as `unknown`, so family-level conclusions from that detector are insufficient evidence. Header inspection confirms the wide area/production/yield structure. There are no missing values according to the report, but negative values occur across the crop measures and are exactly `-1` minima. This strongly suggests sentinel encoding, requiring source confirmation and conversion to missing before modelling.

Zero values vary by crop and can represent no cultivation, no production, or missing-style encoding. For example, Rabi Sorghum yield has 12,113 zeros, while Rice yield has 1,143 zeros. These are not interchangeable. Validate each crop triplet using area, production, and yield identities and source notes.

## 11. Post-Harvest Loss Analysis

The Haryana/Punjab loss table has 164 rows from 2022, two states, 12 crops/commodities, 17 stages, and three loss types. Farm Operations is 53.66%, Market Operations 39.63%, and Total 6.71%. The state-stage table has 1,865 rows from 2022, 19 states, 55 crop/commodity labels, the same 17 stages, and the same three loss types. These tables are structurally complete but source-specific.

The FAO export has 30,361 rows from 2000-2024 and 180 duplicate rows. Its loss percentage ranges from 0 to 65; 63.80% of records use Modelled Estimates as the collection method. Because methods, stages, countries, and units vary, FAO observations should not be directly concatenated with the 2022 extracted tables without a harmonized definition.

Do not mix `Total`, `Overall total loss`, `Total loss in farm operations`, or `Total loss in market operations` with component stages in one training target. This would double count losses. Keep source, table, stage, and loss type as modelling dimensions.

## 12. Dataset Relationships & Integration Possibilities

| Potential integration | Common key required | Main risk | Recommendation |
|---|---|---|---|
| Production + SoilGrids | Spatial assignment from lat/long to district or coordinates; crop/year alignment | SoilGrids has no district key and no time | Do not merge yet; build a documented spatial lookup first |
| Production + soil-nutrient survey | State/district/block/village code plus compatible year | Soil survey uses coded geography and only two years; production uses different labels/periods | Validate code dictionaries and aggregate to a common geography before joining |
| Production + post-harvest loss | Crop, state, year, possibly stage | 2022 loss tables are aggregate/source-table observations, not necessarily district-year observations | Use for supporting analysis or a separate loss model unless the grain is proven compatible |
| Production + FAO loss | Commodity/crop taxonomy, country/region, year, stage, unit definition | FAO is international and methodologically heterogeneous | Harmonize taxonomy and source method; avoid row-level joins by name alone |
| Production + weather | District/coordinate, crop, season, date/year | No weather dataset is currently present in `DataSets` | Acquire/align weather before claiming suitability or yield integration |
| SoilGrids depth layers | Latitude, longitude, depth interval | Potential coordinate precision and duplicate alignment issues | Safe candidate; validate keys and use long canonical form |
| Two production panels | State, district, crop, season, year after normalization | Different crop vocabularies, year formats, units, coverage | Reconcile with a key audit; retain both until proven redundant |
| Two 2022 loss tables | State, crop, stage, loss type, year | Different geography and source table grain | Compare definitions; do not append blindly |

## 13. ML Readiness

| Component | Candidate data and target | Features | Exclude/risks | Split strategy |
|---|---|---|---|---|
| Crop Yield Prediction | National 1997-2019 or Haryana/Punjab 1997-2019; target `Yield` | Crop, state/district, season, year, area after unit review, validated soil/weather | Exclude `Production` if yield is derived; handle missing production and unit mixtures | Time-based holdout plus grouped geography/crop checks; avoid random leakage across repeated locations |
| Crop Suitability Classification | No single confirmed suitability-labelled file is currently present; soil-nutrient labels are nutrient status, not crop suitability | Soil pH/N/P/K, weather, crop label only after a defensible target is created | Do not treat nutrient level as crop suitability without a label definition | INSUFFICIENT EVIDENCE until target construction is specified; use grouped spatial split later |
| Market Price Prediction | No market-price CSV is present in current `DataSets` | Crop, market, state, date, historical price lags | Dataset is absent; cannot define a verified target/features | INSUFFICIENT EVIDENCE; acquire price data first and use chronological split |
| Post-Harvest Loss Prediction | 2022 loss tables or FAO export; target loss percentage | Crop/commodity, state/region, stage, loss type, year, method | Source and measurement definitions differ; totals may double count; sparse metadata | Group by source and stage; time split is limited because 2022 tables are one year |
| Clustering | SoilGrids or aggregated soil-nutrient features | Validated continuous soil properties; coordinate-derived geography only if appropriate | Do not include arbitrary IDs/codes; scale features; handle high correlation | Fit on training geography or spatially held-out samples; interpret clusters agriculturally |
| Anomaly Detection | Production or soil measurements after sentinel/unit cleaning | Domain-valid continuous measures plus context keys | Anomalies may be valid large farms or rare soils; do not delete automatically | Validate flagged records by crop, state, depth, and source; use robust methods |

## 14. Cleaning Plan

### KEEP AS IS

- Raw CSV parts and raw dataset content.
- Source provenance fields in post-harvest and FAO data.
- SoilGrids depth fields and coordinate precision.
- Identifier fields, stored as identifiers rather than continuous predictors.

### CLEAN

- Trim whitespace in national crop/season/state categories; the Kaggle mirror visibly contains padded season and state values.
- Normalize state names such as `Telangana ` and `Jammu and Kashmir ` only in derived copies, preserving raw values.
- Validate and impute or exclude missing production only after source investigation.
- Recode confirmed ICRISAT `-1` sentinels to missing in a cleaned copy.
- Separate or flag zero production/yield/value by domain and nutrient/crop.
- Remove or investigate the 180 duplicate FAO rows using a source-aware key.

### TRANSFORM

- Parse agricultural year labels into a canonical year representation while retaining the original label.
- Normalize area and production units.
- Convert ICRISAT wide crop triplets to long format in a processed copy.
- Reshape SoilGrids to long depth-aware form, then derive a wide feature matrix when required.
- Encode categorical variables with train-only fitted encoders.
- Log-transform highly skewed area/production/loss features only after zero treatment is defined.
- Split soil nutrient `value` by nutrient name and attach nutrient-specific unit metadata.

### DROP FROM MODEL FEATURES

- Raw IDs, administrative codes, source page/table/row numbers, and file-specific row IDs, unless used for grouping or joins.
- `Production` from a yield model when it is target-derived.
- Total-loss rows when modelling component stages, and component rows when modelling a total, to avoid double counting.
- Features unavailable at prediction time.

### INVESTIGATE

- Cross-dataset production duplicates and row-key equivalence.
- ICRISAT negative sentinel semantics.
- Soil-nutrient code dictionaries and nutrient-specific units.
- National production year labels that extend beyond the filename’s stated range.
- Whether `Yield` is consistently defined and unit-compatible across sources.
- Spatial mapping from SoilGrids coordinates to production districts.
- FAO duplicate rows and measurement methods.

## 15. Recommended Data Architecture

```text
DataSets/              immutable raw CSVs and split raw parts
    |
    v
EDA scripts + reports/  inventory, quality checks, plots, interpretation
    |
    v
data_cleaned/         normalized names, units, sentinels, missingness flags
    |
    v
data_processed/      long/wide modelling tables and validated joins
    |
    v
ML datasets             target-specific train/validation/test tables
    |
    v
models/                 fitted preprocessing + model pipelines
    |
    v
backend/API             validated prediction contracts
    |
    v
frontend/dashboard      plots, comparisons, and recommendations
```

Raw files should never be edited in place. Each cleaning decision should be reproducible in a script with a data dictionary, row-count checks, unit checks, and a change log. `reports/` and `plots/` are evidence artifacts, not cleaned modelling inputs.

## 16. Exact Next Steps

### PHASE 1 — EDA interpretation

1. Add the missing dataset-level reports for split soil parts as one logical dataset, if needed.
2. Produce cross-file key audits for the four production panels.
3. Produce a source-aware duplicate audit for the FAO loss file.
4. Validate ICRISAT `-1` semantics and derive crop-triplet consistency checks.
5. Document soil-nutrient code meanings and nutrient-specific units.

### PHASE 2 — Data cleaning

6. Create `data_cleaned/` without changing `DataSets/`.
7. Normalize categorical whitespace/spelling and preserve raw-to-clean mappings.
8. Add missingness flags and source provenance.
9. Convert confirmed sentinels to missing and investigate zero semantics.
10. Decide treatment for incomplete production rows per target.

### PHASE 3 — Data standardization

11. Canonicalize year and agricultural-year fields.
12. Harmonize area, production, yield, and loss units.
13. Create crop and state crosswalks.
14. Create a nutrient dictionary with valid ranges and units.
15. Validate SoilGrids coordinate precision and create the depth-aware long table.

### PHASE 4 — Dataset integration

16. Build spatial lookup logic for SoilGrids-to-district mapping.
17. Join only on documented geography, time, crop, and stage keys.
18. Compare row counts and duplicate keys before and after each join.
19. Keep source datasets separate where grain or measurement definitions are incompatible.

### PHASE 5 — Feature engineering

20. Build leakage-safe yield features excluding target-derived production.
21. Create soil depth summaries only after deciding whether the model needs layer-specific or aggregated features.
22. Create lag and rolling features for market prices after acquiring the market dataset.
23. Create loss-stage features without mixing totals and components.

### PHASE 6 — ML dataset creation

24. Create one target-specific processed dataset for each planned component.
25. Fit imputers, encoders, scalers, and transformations on training data only.
26. Freeze schemas and API contracts with feature names, units, and valid ranges.
27. Write data validation tests for row counts, ranges, categories, and leakage columns.

### PHASE 7 — Model training

28. Only after the previous phases, train baseline and candidate models.
29. Use time- or group-aware validation appropriate to each component.
30. Compare metrics, error slices, and data coverage before saving pipelines.

### Critical Findings

- `Production` is missing in 1.45%-15.09% of production panels and may leak the yield target; it must not automatically be a yield feature.
- ICRISAT contains exact `-1` minima across agricultural measures; these values require sentinel treatment before modelling.
- Soil-nutrient `value` mixes 12 different nutrient concepts and units; global numeric interpretation is invalid.
- Soil-nutrient records cover only 2023-24 and 2024-25, despite their very large row count.
- The six SoilGrids layers are schema-compatible and coordinate-aligned by current checks, but need a depth-aware reshape and spatial lookup before integration.
- Production datasets overlap conceptually but have different crops, years, units, and schemas; redundancy has not been proven.
- Post-harvest component and total rows coexist; combining them without source/stage controls can double count loss.
- No verified market-price dataset or crop-suitability target is present in the inspected `DataSets/` files.

### Questions Requiring Investigation

- Does ICRISAT `-1` definitively mean missing/not available for every crop column?
- Is production-derived yield calculated identically across all production files, and are the yield units compatible?
- What do the coded soil-nutrient name/location fields map to, and what are the units/ranges for each nutrient?
- Are the two production files from the same source/version, and what normalized keys overlap?
- Are FAO duplicate rows independent observations or duplicated exports?
- How should SoilGrids coordinates be assigned to production districts?
- What market-price source and crop-suitability label will be used?
- Are the 2020-21 rows in the file named `1997_2019` valid, and should the filename/metadata be corrected in a derived copy?

### Next Coding Tasks

1. `eda/audit_production_keys.py` — normalize and compare production-panel keys without editing raw data.
2. `eda/validate_icrisat_sentinels.py` — inspect `-1`, zero, and area-production-yield identities by crop.
3. `eda/profile_soil_nutrients_chunked.py` — full-file nutrient-specific units, ranges, duplicates, and location repetition.
4. `eda/validate_soilgrids_layers.py` — coordinate-key alignment and depth consistency.
5. `eda/build_crosswalks.py` — state, district, crop, season, and agricultural-year mappings.
6. `cleaning/clean_production.py` — create cleaned production copies with explicit missingness and units.
7. `cleaning/clean_soil.py` — create nutrient-specific and depth-aware cleaned soil data.
8. `integration/build_spatial_lookup.py` — assign SoilGrids coordinates to a documented geography.
9. `processing/create_yield_ml_dataset.py` — create leakage-safe yield data only after validation.
10. `processing/create_loss_ml_dataset.py` — separate component-stage and total-loss targets.
11. `validation/test_data_contracts.py` — automated schema, range, and leakage checks.

This report is an interpretation of the evidence currently available. Where source semantics, cross-file keys, spatial mapping, or target definitions are not proven, the appropriate conclusion is `INSUFFICIENT EVIDENCE` rather than a guess.
