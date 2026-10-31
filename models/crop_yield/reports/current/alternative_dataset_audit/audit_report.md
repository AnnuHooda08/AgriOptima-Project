# Crop Yield Alternative Dataset Audit (Milestone 2)

## Scope and handling

This audit reads the four CSV files in `DataSets/Yeild/`. The raw files, production Random Forest, Decision Tree challenger, backend, and frontend were not changed. Audit outputs are created only in this folder. Source hashes are in `dataset_inventory.csv`.

Candidate: `district_wise_season_wise_crop_production_1997.csv`. It has **246,091 rows × 7 columns**, years **1997–2015**, 33 state/UT labels, 646 district labels, 124 crop labels, and 6 season labels. The name “1997” does not describe its full coverage: observed rows span 1997–2015.

## Dataset inventory

See `dataset_inventory.csv` for columns, exact dimensions, missing-value counts, file sizes, year ranges, and SHA-256 digests. These four files are distinct formats/coverage rather than interchangeable versions: the candidate is national and long-form; the current source is Haryana/Punjab with explicit unit columns; the 1997–2014 Haryana/Punjab file is another unlabeled-unit long table; ICRISAT is a 1966–2017 wide district panel with explicit 1000-hectare, 1000-tonne and kg/ha columns for selected crops. ICRISAT is not the same table nor a simple superset.

## Measurement unit audit

OGD/DES catalog metadata describes this resource's area as hectares and production as tonnes. The candidate CSV itself has no unit columns. The generic catalog statement cannot be applied blindly because specific crop evidence and record matching expose exceptions:

| Crop group | Original production unit | Evidence and decision | Conversion / yield decision |
|---|---|---|---|
| Coconut | Most likely individual nuts; the exact CSV unit is not explicitly labeled | Coconut Development Board tables report production in million nuts and yield in nuts/ha. Candidate records include 65,100,000 over 18,168 ha, whose scale is consistent with nut counts. This conflicts with the generic OGD tonnes description. | No defensible nuts-to-tonnes conversion for these rows. Kept unresolved; no tonnes/ha calculated. |
| Sugarcane | Tonnes | OGD/DES catalog declares tonnes, and DES national estimates report sugarcane in tonnes. In the Haryana/Punjab overlap, all 470 matched production observations agree. | No conversion; tonnes/ha allowed for valid records. |
| Cotton(lint) | Bales in the overlapping candidate series | 390 overlapping Haryana/Punjab rows with nonmissing production match exactly to the existing dataset, which labels Cotton(lint) as Bales. DES states one cotton bale is 170 kg. | Apply 0.17 tonnes/bale to convert; tonnes/ha allowed after conversion. See per-crop audit ledger. |
| Jute and Mesta | Unresolved in this candidate; official DES statistics use bales of 180 kg | The exact candidate CSV has no unit label and there is no overlap with an explicitly labeled source for these crops. Generic catalog tonnes metadata conflicts with DES crop-specific bale reporting. | No conversion approved for this exact resource; held out of derived yields. |
| Other crops | Tonnes per OGD catalog; no alternate unit convention identified in sources reviewed | The source catalog explicitly declares tonnes and hectares. Crop-specific review found no conflicting convention for remaining candidate crop labels. This is a resource-metadata conclusion, not a guarantee that every source record was independently measured correctly. | No conversion; tonnes/ha permitted for valid records. |

Complete row-level-by-crop evidence appears in `crop_production_unit_audit.csv`. Official references are listed below. `verified_yield_records.csv` contains only positive-area, nonnegative-production records with eligible standardized units. Cotton production is converted using the documented 170 kg/bale factor. Coconut, Jute, and Mesta records are retained separately in `unresolved_unit_records.csv`; no rows are silently dropped from the source.

## Data quality and coverage

Candidate quality checks found **3,730 missing production values**, 0 zero-area rows, 0 negative-area rows, 3,523 zero-production rows, and 0 negative-production rows. Exact full-row duplicates: **0**. Duplicate state–district–year–season–crop key rows: **0** across 0 groups. The script retains all of these records for review.

There are 237,205 eligible derived yields across 120 crops. 5,245 Coconut/Jute/Mesta rows remain in the unresolved-unit file. Another 3,641 rows with otherwise eligible units lack valid positive area or nonnegative numeric production and are itemized in `invalid_or_missing_unit_eligible_records.csv`.

Whitespace in labels (for example padded season/crop/state labels) is normalized only in scratch matching keys; original labels remain intact. Coverage and crop representation by year are provided as CSVs. `yield_iqr_review.csv` contains 7,570 statistical flags for crops with at least 30 records; these are review prompts, not evidence of bad data. `extreme_observation_review.csv` lists 539 within-crop top 0.1% area/production observations with original CSV row numbers. They are retained and require source context before being called errors. The saved plots distinguish verified yield summaries from raw production totals, which are not comparable across unit types.

## Comparison with existing Haryana/Punjab dataset

Exact normalized key matching used State, District, Crop, Season, and the candidate numeric year against the first year in the existing `YYYY-YY` string. It found **8,833 overlapping rows**, with 8,584 matching area values and 7,263 matching production values. Full match detail and per-state/crop summaries are saved as `haryana_punjab_record_matches.csv` and `overlap_summary.csv`.

Matching is informative but does not prove that the two tables are globally identical. The current source has 12,447 Haryana/Punjab rows, explicit Hectare/Tonnes/Bales columns and 1,418 missing production values. The national candidate has broader geographic coverage and 3,730 missing production values. It also includes unit ambiguities. The candidate cannot be appended wholesale without controlling crop units, year conventions, duplicate keys, and the named district/state changes.

## Modelling suitability (no model trained)

The candidate covers 19 calendar years. Crop support is uneven: **77 crops** have at least 100 records, **21** have 30–99, and **26** have fewer than 30. District history is broader but not uniform: 613 of 646 state–district labels appear in at least five distinct years; 5 appear in only one year. The final year, 2015, contains only 562 records, so it would be a thin holdout by itself. Chronological validation is feasible for well-represented crop groups, but not all 124 crops or all districts support stable separate estimates.

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
