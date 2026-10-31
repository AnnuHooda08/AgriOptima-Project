# Crop Yield Model — Final Model Selection Review

**Scope:** This is a validation-only review. It evaluates years through 2014; it does not score or inspect 2015-2019 final-test metrics. It does not train or replace saved artifacts.

## Recommendation

**Do not promote the Decision Tree challenger yet.** Keep the existing Random Forest artifact in place as requested, but do not treat it as validated for future/farm-specific decisions: on the requested 2012-2014 chronological validation, its six-feature configuration is unstable (MAE 8.713, RMSE 48.103, R² -5.667). The crop-season Decision Tree has the best validation MAE among A models, but it substantially underpredicts high-yield Sugarcane and ignores district, year and area. Feature/model rankings also change across earlier time windows.

The extra review does not establish a robust replacement. For a future harvest estimate, the slightly best main-window result is configuration C with Linear Regression (MAE 2.522, RMSE 6.409, R² 0.882), effectively tied with configuration A's Decision Tree (MAE 2.530, RMSE 6.438, R² 0.881). That 0.008 t/ha MAE gap is too small to justify a confident selection given the temporal instability. None of these candidates is truly farm-specific because the records are district-level and contain no matched soil, weather, irrigation, or management data.

## Main chronological validation

Training is 1997-2011 (5,769 rows); validation is 2012-2014 (1,401 rows). The same rows are used across all candidates and feature configurations. All preprocessing is fit only on each training subset. Metrics are tonnes/hectare for MAE/RMSE; higher R² is better.

| Features | Model | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| A: Crop, Season | Decision Tree | 2.5300 | 6.4385 | 0.8806 |
| A: Crop, Season | Linear Regression | 2.5457 | 6.4448 | 0.8803 |
| A: Crop, Season | Lasso | 2.5695 | 6.4583 | 0.8798 |
| A: Crop, Season | Random Forest | 2.6287 | 6.5272 | 0.8772 |
| A: Crop, Season | Ridge | 2.8993 | 6.7740 | 0.8678 |
| B: all six fields | Ridge | 3.3284 | 6.9396 | 0.8612 |
| B: all six fields | Lasso | 3.5685 | 7.0741 | 0.8558 |
| B: all six fields | Linear Regression | 3.7484 | 7.3404 | 0.8448 |
| B: all six fields | Random Forest | 8.7130 | 48.1032 | -5.6670 |
| B: all six fields | Decision Tree | 11.0832 | 74.6629 | -15.0617 |
| C: Crop, Season, YearStart, Area | Linear Regression | **2.5215** | **6.4093** | **0.8816** |
| C: Crop, Season, YearStart, Area | Lasso | 2.5435 | 6.4144 | 0.8815 |
| C: Crop, Season, YearStart, Area | Ridge | 2.8913 | 6.7345 | 0.8693 |
| C: Crop, Season, YearStart, Area | Random Forest | 8.1878 | 47.1470 | -5.4046 |
| C: Crop, Season, YearStart, Area | Decision Tree | 10.5130 | 74.3538 | -14.9290 |

## Feature configurations and use at prediction time

| Configuration | Why consider it | Validation evidence | Available at prediction time? | Use-case fit |
|---|---|---|---|---|
| **A. Crop + Season** | Directly known when a farmer chooses a crop and growing season; creates a transparent crop-season reference. | Decision Tree is best within A: 2.5300 / 6.4385 / 0.8806. | Yes. | A crop-season typical estimate only. It cannot distinguish Punjab from Haryana, districts, years, farm area, or management. |
| **B. State + District + Crop + Season + YearStart + Area** | Uses all existing fields to attempt region/time/scale-specific estimates. State/district and a planned year/area can be known before planting. | Best B is Ridge: 3.3284 / 6.9396 / 0.8612. Tree and forest errors are extreme. | Usually, but Area in the source is observed harvested area. For advance estimates, planned area must be substituted consistently. | District-level estimate, not farm-specific. Area does not describe field conditions. The additional fields hurt the main-window validation comparison. |
| **C. Crop + Season + YearStart + Area** | Tests temporal trend and planned scale without potentially sparse district-specific effects. | Linear Regression is best C: 2.5215 / 6.4093 / 0.8816; marginally ahead of A/Decision Tree by 0.0085 MAE. | Crop, season and year are known; planted area is usually known, though it differs from the recorded harvested-area semantics. | Potential future-year regional-average estimate, not farm-specific. No location or field condition information. |

Production is not included in any configuration because it is used in the target calculation. No new soil or weather fields were invented or joined without aligned records.

## Decision Tree challenger error review

The evaluated tree is the existing Crop+Season candidate with max_depth=None, min_samples_leaf=3. Its fitted tree had **depth 20, 71 nodes and 36 leaves**. Training MAE was 2.337 t/ha and validation MAE was 2.530; the validation MAE gap is modest rather than a classic sign of memorizing the training set. However, train RMSE was 28.661 versus validation RMSE 6.438 because the training years include much more extreme target values. The tree's high depth and the large error swing across time windows remain warning signs.

- **Crop:** Sugarcane had validation MAE **20.464 t/ha** across 90 records, versus **1.299 t/ha** for the other 1,311 records. Actual Sugarcane mean was 75.35 t/ha; mean prediction was 55.37 t/ha. Its 95th-percentile absolute error was 36.43 t/ha.
- **Largest error:** 2012 Panchkula Sugarcane, actual 113.68 t/ha, predicted 55.37 t/ha (under by 58.31 t/ha).
- **Other difficult crops:** Ginger had MAE 13.46 across six rows; Onion 8.17 across 53; Dry chillies 7.07 across 13. These small counts make subgroup estimates uncertain.
- **Season:** Whole Year MAE was 7.90 across 366 rows; Kharif 0.81 across 592; Rabi 0.38 across 443.
- **Region diagnostic:** The tree has no state/district input, so region-specific differences are error summaries only. Haryana MAE was 2.65 and Punjab 2.32. District MAE reached 5.81 in Patiala and 5.80 in Fatehgarh Sahib (21 and 17 records respectively).

The tree predicts learned crop-season groups, so it cannot respond when a particular district/year's Sugarcane yield rises sharply. This is not a farm-specific yield model and its Sugarcane error could be practically large.

A modest parameter check tried max_depth None/5/10 and min_samples_leaf 3/5/10/20. The default setting was already the best on validation; tuning did not fix Sugarcane underprediction.

## Sensitivity to validation years

Three rolling-origin evaluations were run entirely before the final test years. Every fold trains only on years before its validation window.

| Validation years | Training rows | Best model + feature set | MAE | RMSE | R² |
|---|---:|---|---:|---:|---:|
| 2006-2008 | 3,445 | Random Forest + B (all six) | 2.9395 | 61.0611 | 0.0668 |
| 2009-2011 | 4,649 | Lasso + A (Crop, Season) | 3.5975 | 11.1989 | 0.1299 |
| 2012-2014 | 5,769 | Linear Regression + C | 2.5215 | 6.4093 | 0.8816 |

The winning configuration/model changes in every window. The first two periods have very high RMSE and low R² despite moderate MAE, showing that a small number of extreme yield errors dominate squared-error performance. **The decision-tree conclusion is sensitive to which historical years are used.** None of these folds includes 2015-2019.

## Plots and complete outputs

- [Actual vs predicted validation plot](plots/decision_tree_actual_vs_predicted.png)
- [Crop-wise validation error plot](plots/decision_tree_error_by_crop.png)
- [Tree structure, first three levels](plots/decision_tree_structure_depth3.png)
- [Full validation comparison CSV](validation_model_feature_comparison.csv)
- [Rolling-origin scores for every model/configuration](rolling_validation_robustness.csv)
- [Crop, state, district and season error tables](decision_tree_errors_by_crop.csv)
- [Largest individual validation errors](decision_tree_largest_validation_errors.csv)
- [Machine-readable summary](review_summary.json)

## Final recommendation and review gate

Keep the current Random Forest artifact as the production artifact **without endorsing it as robust**; its poor 2012-2014 six-feature validation score needs attention. Keep the Decision Tree challenger separate and do **not** promote it yet. The Crop+Season tree is interpretable and has good aggregate main-window MAE, but severe Sugarcane errors and unstable rolling-window results make it risky for a farmer-facing production estimate. Configuration C's Linear Regression narrowly wins the primary validation, but the advantage over A is negligible and it also lacks geography and field conditions.

The two artifacts were not written by this review. No other ML module or frontend was touched. Wait for explicit approval before replacing the production model or proceeding elsewhere.
